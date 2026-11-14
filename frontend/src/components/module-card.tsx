import { StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing } from '@/constants/theme';

type ModuleCardProps = {
  icon: string;
  title: string;
  description: string;
};

export function ModuleCard({ icon, title, description }: ModuleCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.iconContainer}>
        <Text accessibilityElementsHidden style={styles.icon}>
          {icon}
        </Text>
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.description}>{description}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexGrow: 1,
    flexBasis: '46%',
    minWidth: 140,
    padding: spacing.md,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  iconContainer: {
    width: 38,
    height: 38,
    marginBottom: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.sm,
    backgroundColor: colors.surfaceMuted,
  },
  icon: {
    fontSize: 19,
  },
  title: {
    marginBottom: spacing.xs,
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 19,
  },
});

