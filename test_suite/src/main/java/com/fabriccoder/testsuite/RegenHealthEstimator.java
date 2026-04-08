package com.fabriccoder.testsuite;

/**
 * Pure hunger-regen health estimate from AppleSkin {@code FoodHelper.getEstimatedHealthIncrement(int,float,float)} (Unlicense).
 */
public final class RegenHealthEstimator {

	public static final float REGEN_EXHAUSTION_INCREMENT = 6.0F;
	public static final float MAX_EXHAUSTION = 4.0F;

	private RegenHealthEstimator() {
	}

	public static float getEstimatedHealthIncrement(int foodLevel, float saturationLevel, float exhaustionLevel) {
		float health = 0;

		if (!Float.isFinite(exhaustionLevel) || !Float.isFinite(saturationLevel))
			return 0;

		while (foodLevel >= 18) {
			while (exhaustionLevel > MAX_EXHAUSTION) {
				exhaustionLevel -= MAX_EXHAUSTION;
				if (saturationLevel > 0)
					saturationLevel = Math.max(saturationLevel - 1, 0);
				else
					foodLevel -= 1;
			}
			if (foodLevel >= 20 && Float.compare(saturationLevel, Float.MIN_NORMAL) > 0) {
				float limitedSaturationLevel = Math.min(saturationLevel, REGEN_EXHAUSTION_INCREMENT);
				float exhaustionUntilAboveMax = Math.nextUp(MAX_EXHAUSTION) - exhaustionLevel;
				int numIterationsUntilAboveMax = Math.max(1, (int) Math.ceil(exhaustionUntilAboveMax / limitedSaturationLevel));

				health += (limitedSaturationLevel / REGEN_EXHAUSTION_INCREMENT) * numIterationsUntilAboveMax;
				exhaustionLevel += limitedSaturationLevel * numIterationsUntilAboveMax;
			} else if (foodLevel >= 18) {
				health += 1;
				exhaustionLevel += REGEN_EXHAUSTION_INCREMENT;
			}
		}

		return health;
	}
}
