/** Monorepo PostCSS entry point; the Admin app owns its Tailwind source scan. */
module.exports = {
  plugins: {
    tailwindcss: { config: "./apps/admin-web/tailwind.config.ts" },
  },
};
