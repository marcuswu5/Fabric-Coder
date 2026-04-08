package com.fabriccoder.testsuite;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RegenHealthEstimatorTest {

	@Test
	void nonFiniteInputs_returnZero() {
		assertEquals(0f, RegenHealthEstimator.getEstimatedHealthIncrement(20, Float.NaN, 0f), 0f);
		assertEquals(0f, RegenHealthEstimator.getEstimatedHealthIncrement(20, 1f, Float.POSITIVE_INFINITY), 0f);
	}

	@Test
	void belowRegenThreshold_returnsZero() {
		assertEquals(0f, RegenHealthEstimator.getEstimatedHealthIncrement(17, 10f, 0f), 0f);
	}

	@Test
	void slowRegen_oneTickAtHunger18_zeroSaturation() {
		assertEquals(1f, RegenHealthEstimator.getEstimatedHealthIncrement(18, 0f, 0f), 1e-5f);
	}

	@Test
	void constants_matchAppleSkin() {
		assertEquals(6.0f, RegenHealthEstimator.REGEN_EXHAUSTION_INCREMENT, 0f);
		assertEquals(4.0f, RegenHealthEstimator.MAX_EXHAUSTION, 0f);
	}

	@Test
	void deterministicForFixedInputs() {
		float a = RegenHealthEstimator.getEstimatedHealthIncrement(19, 2.5f, 1.25f);
		float b = RegenHealthEstimator.getEstimatedHealthIncrement(19, 2.5f, 1.25f);
		assertEquals(a, b, 0f);
		assertTrue(Float.isFinite(a));
	}
}
