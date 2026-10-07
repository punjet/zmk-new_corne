if(CONFIG_EYELASH_LED_TEST)
  zephyr_library_include_directories(${CMAKE_SOURCE_DIR}/include)
  zephyr_library_sources(led_test.c)
endif()
