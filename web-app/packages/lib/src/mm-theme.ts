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
    }
  },
  {}
)
