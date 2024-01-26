import { AutoCompletePassThroughOptions } from 'primevue/autocomplete'
import { ButtonPassThroughOptions } from 'primevue/button'
import { DataViewPassThroughOptions } from 'primevue/dataview'
import { InputTextPassThroughOptions } from 'primevue/inputtext'
import { usePassThrough } from 'primevue/passthrough'
import { PasswordPassThroughOptions } from 'primevue/password'
import { ToastPassThroughOptions } from 'primevue/toast'

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
    } as ButtonPassThroughOptions,
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
    } as AutoCompletePassThroughOptions,
    toast: {
      root: {
        style: {
          maxWidth: '40rem',
          width: '80%'
        }
      }
    } as ToastPassThroughOptions,
    dataview: {
      header: {
        class: 'px-4 py-2'
      },
      loadingOverlay: {
        class: 'bg-primary-reverse opacity-50'
      }
    } as DataViewPassThroughOptions,
    inputText: {
      root: {
        class: 'border-round-xl'
      }
    } as InputTextPassThroughOptions,
    password: {
      root: {
        class: 'w-full'
      },
      input: { root: { class: 'w-full border-round-xl' } }
    } as PasswordPassThroughOptions
  },
  {}
)
