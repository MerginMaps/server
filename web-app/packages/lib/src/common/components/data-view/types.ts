export interface DataViewWrapperOptions {
  sortDesc?: boolean
  sortBy?: string
  page?: number
  itemsPerPage: number
}

export interface DataViewWrapperColumnItem {
  text: string
  value: string
  cols?: number
  fixed?: boolean
  textClass?: string
}
