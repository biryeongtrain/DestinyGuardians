package kim.biryeong.destiny.campaign.presentation;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DeparturePathTest {
    @Test void liftsFirstThenBoostsWithoutJumps() {
        double[] lift = Departure.path(Departure.LIFT);
        assertEquals(0, lift[0], 1e-9, "no forward motion while lifting");
        assertEquals(Departure.LIFT_HEIGHT, lift[1], 1e-9);
        double[] end = Departure.path(Departure.FLIGHT);
        assertEquals(Departure.BOOST_DISTANCE, end[0], 1e-9);
        // Position and speed are continuous at every tick: no teleport-like step anywhere.
        double prevStep = 0;
        for (double t = 0; t < Departure.FLIGHT; t += .25) {
            double[] a = Departure.path(t), b = Departure.path(t + .25);
            double step = Math.hypot(b[0] - a[0], b[1] - a[1]);
            assertTrue(Math.abs(step - prevStep) < .35, "speed jump at t=" + t + ": " + prevStep + " -> " + step);
            assertTrue(Math.abs(b[2] - a[2]) < 1.0, "pitch jump at t=" + t);
            prevStep = step;
        }
    }

    @Test void tallHangarsLiftHigherAndStaySmooth() {
        var f = Departure.Flight.of(40);
        assertTrue(f.liftTicks() > Departure.LIFT, "a taller climb takes longer");
        assertEquals(40, Departure.path(f, f.liftTicks())[1], 1e-9);
        assertEquals(0, Departure.path(f, f.hoverTicks())[0], 1e-9, "no forward motion before the boost");
        double prev = 0;
        for (double t = 0; t < f.total(); t += .25) {
            double[] a = Departure.path(f, t), b = Departure.path(f, t + .25);
            double step = Math.hypot(b[0] - a[0], b[1] - a[1]);
            assertTrue(Math.abs(step - prev) < .5, "speed jump at t=" + t);
            prev = step;
        }
        assertEquals(Departure.MAX_LIFT, Departure.Flight.of(500).lift(), 1e-9);
    }
}
