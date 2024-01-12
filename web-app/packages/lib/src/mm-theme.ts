import { usePassThrough } from 'primevue/passthrough'

export default usePassThrough(
  {
    button: {
      root(options) {
        return {
          class: [
            'line-height-4',
            options.props.plain ? 'hover:text-color' : undefined
          ],
          style:
            options.context.disabled && !options.props.severity
              ? {
                  backgroundColor: 'var(--medium-green-color)',
                  borderColor: 'var(--medium-green-color)'
                }
              : undefined
        }
      }
    },
    autocomplete: {
      root: {
        class: 'w-full'
      },
      container: {
        class: 'border-round-xl w-full'
      },
      token: {
        class: 'text-color-forest text-xs font-semibold',
        style: {
          backgroundColor: 'var(--medium-green-color)'
        }
      },
      tokenLabel: {
        class: 'mr-2'
      }
    }
  },
  {}
)
