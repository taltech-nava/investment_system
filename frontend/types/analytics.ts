export interface DistributionResult {
  bins: number[];
  all: number[];
  selected: number[];
  mean_all: number | null;
  mean_selected: number | null;
  significant: boolean;
  p_value: number | null;
}

export interface ReportRowResult {
  report_id: number;
  forecast_id: number;
  review_date: string;
  prediction_date: string;
  ticker: string;
  instrument_name: string;
  publisher_id: number;
  publisher_name: string | null;
  forecast_price: number;
  realised_price: number;
  error_ratio: number;
  error_percent: number;
  direction_correct: boolean | null;
  method: string | null;
}

export interface ReportsPageResult {
  items: ReportRowResult[];
  page: number;
  page_size: number;
  total: number;
}
