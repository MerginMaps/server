import { AutoCompletePassThroughOptions } from 'primevue/autocomplete'
import { ButtonPassThroughOptions } from 'primevue/button'
import { DataViewPassThroughOptions } from 'primevue/dataview'
import { DialogPassThroughOptions } from 'primevue/dialog'
import { InlineMessagePassThroughOptions } from 'primevue/inlinemessage'
import { InputTextPassThroughOptions } from 'primevue/inputtext'
import { MenuPassThroughOptions } from 'primevue/menu'
import { usePassThrough } from 'primevue/passthrough'
import { PasswordPassThroughOptions } from 'primevue/password'
import { ProgressBarPassThroughOptions } from 'primevue/progressbar'
import { TagPassThroughOptions } from 'primevue/tag'
import { ToastPassThroughOptions } from 'primevue/toast'
import { TreePassThroughOptions } from 'primevue/tree'

export default usePassThrough(
  {
    button: {
      root(options) {
        return {
          class: [options.props.plain ? 'hover:text-color' : undefined],
          style: {
            lineHeight: 1.857,
            ...(options.context.disabled && !options.props.severity
              ? {
                  backgroundColor: 'var(--medium-green-color)',
                  borderColor: 'var(--medium-green-color)'
                }
              : undefined)
          }
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
        class: 'text-color-forest title-t4',
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
        class: 'px-4 py-1'
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
    } as PasswordPassThroughOptions,
    progressBar: {
      root: {
        style: {
          backgroundColor: 'var(--primary-color)',
          borderRadius: '20px'
        }
      },
      value(options) {
        return {
          style: {
            backgroundColor:
              options.props.value > 100
                ? 'var(--negative-color)'
                : 'var(--forest-color)',
            borderRadius: '20px'
          }
        }
      }
    } as ProgressBarPassThroughOptions,
    tree: {
      root: 'surface-ground border-none p-0',
      content(options) {
        return {
          class: [
            'border-round-xl p-2 title-t3',
            options.context.selected
              ? 'text-white'
              : 'surface-section hover:surface-50'
          ],
          style: {
            backgroundColor: options.context.selected
              ? 'var(--forest-color)'
              : undefined
          }
        }
      }
    } as TreePassThroughOptions,
    inlineMessage: {
      root: 'justify-content-start font-semibold'
    } as InlineMessagePassThroughOptions,
    dialog: {
      header: {
        class: 'border-none border-round-top-2xl',
        style: {
          color: 'var(--forest-color)'
        }
      },
      title: {
        class: 'title-t2'
      },
      closeButton:
        'text-2xl hover:surface-ground text-color-forest hover:text-color',
      content: {
        class: 'border-round-bottom-2xl'
      },
      mask: {
        style: { zIndex: 7 }
      }
    } as DialogPassThroughOptions,
    menu: {
      label: 'title-t4'
    } as MenuPassThroughOptions,
    tag: {
      root: 'title-t5',
      value: 'title-t5'
    } as TagPassThroughOptions
  },
  {}
)
