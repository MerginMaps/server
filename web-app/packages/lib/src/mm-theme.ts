import { AccordionPassThroughOptions } from 'primevue/accordion'
import { AutoCompletePassThroughOptions } from 'primevue/autocomplete'
import { ButtonPassThroughOptions } from 'primevue/button'
import { ColumnPassThroughOptions } from 'primevue/column'
import { DataTablePassThroughOptions } from 'primevue/datatable'
import { DataViewPassThroughOptions } from 'primevue/dataview'
import { DialogPassThroughOptions } from 'primevue/dialog'
import { InlineMessagePassThroughOptions } from 'primevue/inlinemessage'
import { InputTextPassThroughOptions } from 'primevue/inputtext'
import { MenuPassThroughOptions } from 'primevue/menu'
import { usePassThrough } from 'primevue/passthrough'
import { PasswordPassThroughOptions } from 'primevue/password'
import { ProgressBarPassThroughOptions } from 'primevue/progressbar'
import { TabPanelPassThroughOptions } from 'primevue/tabpanel'
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
      root(options) {
        const isBottom = ['bottom', 'bottomright', 'bottomleft'].some(
          (item) => item === options?.props?.position
        )
        return {
          style: { marginBottom: isBottom ? 0 : null }
        }
      },
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
      content(options) {
        const isBottom = ['bottom', 'bottomright', 'bottomleft'].some(
          (item) => item === options?.props?.position
        )
        return isBottom ? '' : 'border-round-bottom-2xl'
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
    } as TagPassThroughOptions,
    column: {
      bodyCell: {
        class: 'pl-4 py-2'
      },
      headerCell: {
        class: 'pl-4 py-1',
        style: {
          backgroundColor: '#F8F9FA'
        }
      },
      headerTitle: {
        class: 'paragraph-p6'
      }
    } as ColumnPassThroughOptions,
    dataTable: {
      loadingOverlay: {
        class: 'bg-primary-reverse opacity-50'
      },
      bodyRow: {
        class: 'paragraph-p6 hover:bg-gray-50 cursor-pointer'
      }
    } as DataTablePassThroughOptions,
    accordion: {
      accordiontab: {
        headerAction: {
          class: 'border-noround border-x-none'
        }
      }
    } as AccordionPassThroughOptions,
    tabPanel: {
      headerAction({ context }) {
        // Custom handling of active styles for tabs
        return {
          style: {
            backgroundColor: 'transparent',
            borderBottomColor: context?.active
              ? 'var(--forest-color)'
              : 'transparent'
          },
          class: [
            'hover:border-400 pb-4',
            { 'text-color-forest': context?.active }
          ]
        }
      }
    } as TabPanelPassThroughOptions
  },
  {}
)
