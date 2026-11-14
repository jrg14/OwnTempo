import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { HealthCard } from '@/components/health-card';
import { ModuleCard } from '@/components/module-card';
import { colors, radii, spacing } from '@/constants/theme';
import { useHealthCheck } from '@/hooks/use-health-check';

const modules = [
  { icon: '✓', title: 'Tareas', description: 'Organiza lo que tienes pendiente.' },
  { icon: '○', title: 'Calendario', description: 'Ten tus planes siempre a mano.' },
  { icon: '+', title: 'Compra', description: 'Comparte listas sin complicaciones.' },
  { icon: '€', title: 'Gastos', description: 'Separa lo personal de lo común.' },
];

export function HomeScreen() {
  const health = useHealthCheck();

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView
        alwaysBounceVertical={false}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.container}>
          <View style={styles.brandRow}>
            <View style={styles.logoMark}>
              <View style={styles.logoDot} />
            </View>
            <Text style={styles.brand}>OwnTempo</Text>
            <View style={styles.previewBadge}>
              <Text style={styles.previewText}>PRIMERA VERSIÓN</Text>
            </View>
          </View>

          <View style={styles.hero}>
            <View pointerEvents="none" style={styles.heroCircleLarge} />
            <View pointerEvents="none" style={styles.heroCircleSmall} />
            <Text style={styles.heroEyebrow}>TU VIDA, A TU RITMO</Text>
            <Text style={styles.heroTitle}>Todo lo importante, en un solo lugar.</Text>
            <Text style={styles.heroDescription}>
              Organiza tu día a día y comparte solo lo que quieras con tu pareja,
              familia o compañeros de piso.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Una aplicación que se adapta a ti</Text>
            <Text style={styles.sectionDescription}>
              Activa los módulos que necesites y úsalos de forma personal o compartida.
            </Text>
            <View style={styles.moduleGrid}>
              {modules.map((module) => (
                <ModuleCard key={module.title} {...module} />
              ))}
            </View>
          </View>

          <View style={styles.spacesCard}>
            <View style={styles.spacesIllustration}>
              <View style={[styles.avatar, styles.avatarBack]} />
              <View style={[styles.avatar, styles.avatarMiddle]} />
              <View style={[styles.avatar, styles.avatarFront]} />
            </View>
            <View style={styles.spacesCopy}>
              <Text style={styles.spacesTitle}>Un espacio para cada parte de tu vida</Text>
              <Text style={styles.spacesDescription}>
                Mantén tus cosas personales separadas y crea espacios comunes para
                organizarte con otras personas.
              </Text>
            </View>
          </View>

          <View style={styles.section}>
            <HealthCard
              checkedAt={health.checkedAt}
              data={health.data}
              error={health.error}
              onRetry={() => void health.refresh()}
              status={health.status}
            />
          </View>

          <Text style={styles.footerText}>OwnTempo · Construyendo con calma</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: spacing.xl,
  },
  container: {
    width: '100%',
    maxWidth: 760,
    alignSelf: 'center',
    paddingHorizontal: spacing.md,
  },
  brandRow: {
    minHeight: 72,
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoMark: {
    width: 30,
    height: 30,
    marginRight: spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    backgroundColor: colors.primary,
  },
  logoDot: {
    width: 10,
    height: 10,
    borderRadius: radii.pill,
    backgroundColor: colors.accent,
  },
  brand: {
    flex: 1,
    color: colors.text,
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.4,
  },
  previewBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radii.pill,
    backgroundColor: colors.surfaceMuted,
  },
  previewText: {
    color: colors.primary,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  hero: {
    minHeight: 330,
    padding: spacing.lg,
    justifyContent: 'flex-end',
    overflow: 'hidden',
    borderRadius: radii.lg,
    backgroundColor: colors.primaryDark,
  },
  heroCircleLarge: {
    position: 'absolute',
    top: -82,
    right: -50,
    width: 230,
    height: 230,
    borderRadius: radii.pill,
    backgroundColor: '#2A7566',
  },
  heroCircleSmall: {
    position: 'absolute',
    top: 38,
    right: 50,
    width: 92,
    height: 92,
    borderRadius: radii.pill,
    backgroundColor: colors.accent,
    opacity: 0.9,
  },
  heroEyebrow: {
    marginBottom: spacing.sm,
    color: '#BBD8D0',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.4,
  },
  heroTitle: {
    maxWidth: 540,
    color: colors.surface,
    fontSize: 38,
    fontWeight: '800',
    letterSpacing: -1.2,
    lineHeight: 43,
  },
  heroDescription: {
    maxWidth: 540,
    marginTop: spacing.md,
    color: '#DDECE8',
    fontSize: 16,
    lineHeight: 24,
  },
  section: {
    marginTop: spacing.xl,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 25,
    fontWeight: '800',
    letterSpacing: -0.6,
  },
  sectionDescription: {
    maxWidth: 560,
    marginTop: spacing.sm,
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 22,
  },
  moduleGrid: {
    marginTop: spacing.lg,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  spacesCard: {
    marginTop: spacing.xl,
    padding: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: '#F1E8DC',
  },
  spacesIllustration: {
    width: 100,
    height: 74,
  },
  avatar: {
    position: 'absolute',
    width: 54,
    height: 54,
    borderWidth: 4,
    borderColor: '#F1E8DC',
    borderRadius: radii.pill,
  },
  avatarBack: {
    top: 2,
    left: 0,
    backgroundColor: '#7DA69C',
  },
  avatarMiddle: {
    top: 18,
    left: 25,
    backgroundColor: colors.accent,
  },
  avatarFront: {
    top: 3,
    left: 48,
    backgroundColor: colors.primary,
  },
  spacesCopy: {
    flex: 1,
  },
  spacesTitle: {
    color: colors.text,
    fontSize: 19,
    fontWeight: '800',
  },
  spacesDescription: {
    marginTop: spacing.xs,
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 21,
  },
  footerText: {
    marginTop: spacing.xl,
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'center',
  },
});

