/**
 * Design tokens cho Smart Driving Assistant Mobile App
 * Nhất quán với web app — dark navy theme, chuyên nghiệp
 */
export const theme = {
  colors: {
    // Backgrounds
    bg:         '#0A0E1A',  // Deepest background
    surface:    '#111827',  // Cards, panels
    elevated:   '#1A2440',  // Raised elements
    overlay:    'rgba(10,14,26,0.92)',

    // Brand
    primary:    '#3B7FFF',
    primaryDim: '#1D4ED8',
    primaryBg:  'rgba(59,127,255,0.12)',

    // Status
    success:    '#10B981',
    successBg:  'rgba(16,185,129,0.12)',
    warning:    '#F59E0B',
    warningBg:  'rgba(245,158,11,0.12)',
    danger:     '#EF4444',
    dangerBg:   'rgba(239,68,68,0.12)',
    info:       '#06B6D4',

    // Borders
    border:       'rgba(255,255,255,0.07)',
    borderHover:  'rgba(255,255,255,0.14)',

    // Text
    text: {
      primary:   '#F1F5F9',
      secondary: '#94A3B8',
      muted:     '#475569',
      disabled:  '#1E293B',
    },
  },

  /* Spacing scale (4px grid) */
  space: {
    xs:  4,
    sm:  8,
    md:  12,
    lg:  16,
    xl:  20,
    '2xl': 24,
    '3xl': 32,
  },

  /* Border radius */
  radius: {
    sm:   6,
    md:   10,
    lg:   14,
    xl:   18,
    full: 9999,
  },

  /* Typography */
  fontSize: {
    xs:   11,
    sm:   12,
    base: 14,
    md:   15,
    lg:   17,
    xl:   20,
    '2xl': 24,
    '3xl': 30,
  },

  fontWeight: {
    normal:    '400' as const,
    medium:    '500' as const,
    semibold:  '600' as const,
    bold:      '700' as const,
    extrabold: '800' as const,
  },
};

export type Theme = typeof theme;

/** Tạo style card chuẩn */
export const cardStyle = {
  backgroundColor: theme.colors.surface,
  borderRadius: theme.radius.lg,
  borderWidth: 1,
  borderColor: theme.colors.border,
};
