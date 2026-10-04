/* C51 teaching example; NOT compiled or tested on user's board.
 * Verify MCU, reg51.h, free P1.0 and electrical load before use.
 * This is approximate software PWM, not a precise signal source.
 * Change DUTY_PERCENT to 25, 50, or 75, then compile separately.
 */
#include <reg51.h>

#define DUTY_PERCENT 50u
#define PERIOD_UNITS 100u

#if (DUTY_PERCENT < 1) || (DUTY_PERCENT > 99)
#error DUTY_PERCENT_must_be_between_1_and_99
#endif

sbit PWM_OUT = P1^0;

static void delay_units(unsigned int units)
{
    unsigned int i;
    volatile unsigned int j;
    for (i = 0; i < units; ++i) {
        for (j = 0; j < 20; ++j) {
            /* No guaranteed real-time unit; measure actual period. */
        }
    }
}

void main(void)
{
    unsigned int high_units;
    unsigned int low_units;

    high_units = (PERIOD_UNITS * DUTY_PERCENT) / 100u;
    low_units = PERIOD_UNITS - high_units;
    PWM_OUT = 0;

    while (1) {
        PWM_OUT = 1;
        delay_units(high_units);
        PWM_OUT = 0;
        delay_units(low_units);
    }
}
