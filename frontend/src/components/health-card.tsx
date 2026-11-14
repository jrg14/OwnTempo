import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { API_BASE_URL, type HealthResponse } from '@/api/health';
import { colors, radii, spacing } from '@/constants/theme';

type HealthCardProps = {
  status: 'checking' | 'online' | 'offline';
  data: HealthResponse | null;
  error: string | null;
  checkedAt: Date | null;
  onRetry: () => void;
};

const statusContent = {
  checking: {
    label: 'Comprobando servicios',
    detail: 'Conectando con el backend de OwnTempo…',
    color: colors.checking,
    backgroundColor: colors.checkingSoft,
  },
  online: {
    label: 'Todos los sistemas operativos',
    detail: 'Django y PostgreSQL responden correctamente.',
    color: colors.success,
    backgroundColor: colors.successSoft,
  },
  offline: {
    label: 'No se puede conectar',
    detail: 'Revisa que el backend esté iniciado y que la URL sea accesible.',
    color: colors.danger,
    backgroundColor: colors.dangerSoft,
  },
} as const;

export function HealthCard({
  status,
  data,
  error,
  checkedAt,
  onRetry,
}: HealthCardProps) {
  const content = statusContent[status];
  const checkedAtLabel = checkedAt?.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <View style={styles.card}>
      <View style={styles.headingRow}>
        <View>
          <Text style={styles.eyebrow}>ESTADO DEL SERVICIO</Text>
          <Text style={styles.title}>Conexión con OwnTempo</Text>
        </View>
        <View
          accessibilityLabel={content.label}
          style={[styles.statusIcon, { backgroundColor: content.backgroundColor }]}
        >
          {status === 'checking' ? (
            <ActivityIndicator color={content.color} size="small" />
          ) : (
            <View style={[styles.statusDot, { backgroundColor: content.color }]} />
          )}
        </View>
      </View>

      <Text style={[styles.statusLabel, { color: content.color }]}>{content.label}</Text>
      <Text style={styles.detail}>{error ?? content.detail}</Text>

      {data ? (
        <View style={styles.checksRow}>
          <Text style={styles.check}>Django · {data.checks.django}</Text>
          <Text style={styles.check}>PostgreSQL · {data.checks.database}</Text>
        </View>
      ) : null}

      <View style={styles.footer}>
        <View style={styles.connectionInfo}>
          <Text numberOfLines={1} style={styles.apiUrl}>
            {API_BASE_URL}
          </Text>
          {checkedAtLabel ? (
            <Text style={styles.checkedAt}>Última revisión: {checkedAtLabel}</Text>
          ) : null}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Volver a comprobar el estado del servicio"
          disabled={status === 'checking'}
          onPress={onRetry}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
            status === 'checking' && styles.buttonDisabled,
          ]}
        >
          <Text style={styles.buttonText}>Comprobar</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    shadowColor: '#123C32',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
    elevation: 3,
  },
  headingRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  eyebrow: {
    marginBottom: spacing.xs,
    color: colors.primary,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  title: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '700',
  },
  statusIcon: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.pill,
  },
  statusDot: {
    width: 11,
    height: 11,
    borderRadius: radii.pill,
  },
  statusLabel: {
    marginTop: spacing.lg,
    fontSize: 16,
    fontWeight: '700',
  },
  detail: {
    marginTop: spacing.xs,
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 21,
  },
  checksRow: {
    marginTop: spacing.md,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  check: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    overflow: 'hidden',
    borderRadius: radii.pill,
    backgroundColor: colors.successSoft,
    color: colors.primaryDark,
    fontSize: 12,
    fontWeight: '600',
  },
  footer: {
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  connectionInfo: {
    flex: 1,
  },
  apiUrl: {
    color: colors.textMuted,
    fontSize: 12,
  },
  checkedAt: {
    marginTop: 3,
    color: colors.textMuted,
    fontSize: 11,
  },
  button: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonText: {
    color: colors.surface,
    fontSize: 13,
    fontWeight: '700',
  },
});

