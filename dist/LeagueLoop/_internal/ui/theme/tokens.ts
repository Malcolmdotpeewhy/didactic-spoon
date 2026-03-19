import { colors } from "./colors";
import { spacing } from "./spacing";
import { typography } from "./typography";
import { shadows } from "./shadows";
import { motion } from "./motion";

export const theme = {
  colors,
  spacing,
  typography,
  shadows,
  motion,
};

export type Theme = typeof theme;
