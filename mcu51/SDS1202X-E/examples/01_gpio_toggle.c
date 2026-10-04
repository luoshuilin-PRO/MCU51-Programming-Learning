/* C51 teaching example; NOT compiled or tested on user's board.
 * Prerequisites: compatible reg51.h, verified free P1.0 GPIO.
 * Software delay has NO guaranteed time unit or output frequency.
 */
#include <reg51.h>

sbit TEST_OUT = P1^0;

static void delay_units(unsigned int units)
{
    unsigned int i;
    volatile unsigned int j;
    for (i = 0; i < units; ++i) {
        for (j = 0; j < 200; ++j) {
            /* Intentional busy wait; verify timing on the oscilloscope. */
        }
    }
}

void main(void)
{
    TEST_OUT = 0;
    while (1) {
        TEST_OUT = 1;
        delay_units(500);
        TEST_OUT = 0;
        delay_units(500);
    }
}
