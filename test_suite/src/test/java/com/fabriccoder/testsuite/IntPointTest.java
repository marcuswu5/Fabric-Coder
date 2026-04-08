package com.fabriccoder.testsuite;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class IntPointTest {

	@Test
	void fieldsHoldCoordinates() {
		IntPoint p = new IntPoint();
		p.x = -3;
		p.y = 14;
		assertEquals(-3, p.x);
		assertEquals(14, p.y);
	}
}
