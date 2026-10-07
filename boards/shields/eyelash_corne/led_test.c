/*
 * LED order test: finds which LED of the WS2812 chain sits under which key.
 * Phase 1: every LED green for 4 s (shows how many LEDs there are and where).
 * Phase 2: one LED at a time, 1.5 s each, colour cycling red/green/blue by index,
 * then repeat. Built only with CONFIG_EYELASH_LED_TEST=y (underglow disabled).
 * SPDX-License-Identifier: MIT
 */

#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/init.h>
#include <zephyr/drivers/led_strip.h>
#include <drivers/ext_power.h>

#define STRIP_NODE DT_CHOSEN(zmk_underglow)
#define NUM_LEDS DT_PROP(STRIP_NODE, chain_length)
#define ALL_ON_MS 4000
#define STEP_MS 1500
#define LEVEL 90

static const struct device *const strip = DEVICE_DT_GET(STRIP_NODE);
static const struct device *const ext_power = DEVICE_DT_GET(DT_INST(0, zmk_ext_power_generic));
static struct led_rgb pixels[NUM_LEDS];
static int step = -1; /* -1 = all on, 0..NUM_LEDS-1 = single LED */

static void tick(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(tick_work, tick);

static void tick(struct k_work *work) {
    if (device_is_ready(ext_power)) {
        ext_power_enable(ext_power);
    }

    memset(pixels, 0, sizeof(pixels));
    if (step < 0) {
        for (int i = 0; i < NUM_LEDS; i++) {
            pixels[i].g = LEVEL;
        }
    } else {
        switch (step % 3) {
        case 0: pixels[step].r = LEVEL; break;
        case 1: pixels[step].g = LEVEL; break;
        default: pixels[step].b = LEVEL; break;
        }
    }
    led_strip_update_rgb(strip, pixels, NUM_LEDS);

    int delay = step < 0 ? ALL_ON_MS : STEP_MS;
    step = step + 1 >= NUM_LEDS ? -1 : step + 1;
    k_work_schedule(&tick_work, K_MSEC(delay));
}

static int led_test_init(void) {
    k_work_schedule(&tick_work, K_SECONDS(2));
    return 0;
}

SYS_INIT(led_test_init, APPLICATION, 99);
