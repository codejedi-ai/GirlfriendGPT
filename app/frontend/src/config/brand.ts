/**
 * Single source of truth for product branding in the Vite UI.
 * Override with `VITE_PRODUCT_NAME` (and optional tagline/stack label) in `.env`.
 */

const fromEnv = (key: keyof ImportMetaEnv, fallback: string): string => {
  const value = import.meta.env[key]
  return typeof value === 'string' && value.trim() ? value.trim() : fallback
}

/** Display name shown in nav, footer, titles, etc. */
export const PRODUCT_NAME = fromEnv('VITE_PRODUCT_NAME', 'GirlfriendGPT')

/** Uppercase mark for hero / section labels. */
export const PRODUCT_NAME_UPPER = PRODUCT_NAME.toUpperCase()

export const PRODUCT_TAGLINE = fromEnv(
  'VITE_PRODUCT_TAGLINE',
  'Where Humans Meet AI',
)

export const PRODUCT_STACK_LABEL = fromEnv('VITE_PRODUCT_STACK_LABEL', 'LOCAL')

export const PRODUCT_FOOTER_CREDIT = fromEnv(
  'VITE_PRODUCT_FOOTER_CREDIT',
  `${PRODUCT_NAME} • Local stack`,
)

export const PRODUCT_DESCRIPTION = fromEnv(
  'VITE_PRODUCT_DESCRIPTION',
  `${PRODUCT_NAME} — local AI companions with voice and text chat.`,
)

export const documentTitle = (): string =>
  `${PRODUCT_NAME} | ${PRODUCT_TAGLINE}`
