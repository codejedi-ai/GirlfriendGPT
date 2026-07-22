/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
  readonly VITE_TALK_API_BASE?: string
  readonly VITE_API_URL?: string
  readonly VITE_BACKEND_PROXY?: string
  /** Product display name (default: GirlfriendGPT). */
  readonly VITE_PRODUCT_NAME?: string
  readonly VITE_PRODUCT_TAGLINE?: string
  readonly VITE_PRODUCT_STACK_LABEL?: string
  readonly VITE_PRODUCT_DESCRIPTION?: string
  readonly VITE_PRODUCT_FOOTER_CREDIT?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
