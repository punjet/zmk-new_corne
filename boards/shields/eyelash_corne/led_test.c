/*
 * LED order test: finds which LED of the WS2812 chain sits under which key.
 * LED 0 stays red as a start marker; a white dot then walks LED 1, 2, ... one step
 * every STEP_MS, pauses, and repeats. Built only with CONFIG_EYELASH_LED_TEST=y.
 * SPDX-License-Identifier: MIT
 */

#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/init.h>
#include <zephyr/drivers/led_strip.h>
#include <drivers/ext_power.h>
#include <zmk/rgb_underglow.h>

#define STRIP_NODE DT_CHOSEN(zmk_underglow)
#define NUM_LEDS DT_PROP(STRIP_NODE, chain_length)
#define STEP_MS 800
#define PAUSE_STEPS 3

static const struct device *const strip = DEVICE_DT_GET(STRIP_NODE);
static const struct device *const ext_power = DEVICE_DT_GET(DT_INST(0, zmk_ext_power_generic));
static struct led_rgb pixels[NUM_LEDS];
static int step;

static void tick(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(tick_work, tick);

static void tick(struct k_work *work) {
    bool underglow_on = false;
    if (zmk_rgb_underglow_get_state(&underglow_on) == 0 && underglow_on) {
        zmk_rgb_underglow_off();
    }
    if (device_is_ready(ext_power)) {
        ext_power_enable(ext_power);
    }

    memset(pixels, 0, sizeof(pixels));
    pixels[0].r = 80;
    if (step >= 1 && step < NUM_LEDS) {
        pixels[step].r = 70;
        pixels[step].g = 70;
        pixels[step].b = 70;
    }
    led_strip_update_rgb(strip, pixels, NUM_LEDS);

    step = (step + 1) % (NUM_LEDS + PAUSE_STEPS);
    k_work_schedule(&tick_work, K_MSEC(STEP_MS));
}

static int led_test_init(void) {
    k_work_schedule(&tick_work, K_SECONDS(3));
    return 0;
}

SYS_INIT(led_test_init, APPLICATION, 99);
