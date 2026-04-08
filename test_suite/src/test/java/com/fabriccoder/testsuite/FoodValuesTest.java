package com.fabriccoder.testsuite;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

class FoodValuesTest {

	@Test
	void saturationIncrement_matchesAppleSkinFormula() {
		assertEquals(0f, new FoodValues(0, 1f).getSaturationIncrement(), 1e-6f);
		assertEquals(4f, new FoodValues(4, 0.5f).getSaturationIncrement(), 1e-6f);
		assertEquals(20f, new FoodValues(10, 1f).getSaturationIncrement(), 1e-6f);
	}

	@Test
	void equals_andHashCode_useHungerAndModifier() {
		FoodValues a = new FoodValues(3, 0.25f);
		FoodValues b = new FoodValues(3, 0.25f);
		FoodValues c = new FoodValues(3, 0.5f);
		assertEquals(a, b);
		assertEquals(a.hashCode(), b.hashCode());
		assertNotEquals(a, c);
	}
}
