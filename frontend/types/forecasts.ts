export interface ForecastOptions {
  estimate_types: string[];
  scenarios: string[];
}

export interface ForecastRead {
  id: number;
  instrument_id: number;
  scenario: string | null;
  predicted_price: number;
  maturation_date: string;
  prediction_date: string;
  currency: string;
  publisher_id: number;
  conviction: number | null;
  conviction_source: string | null;
  horizon_source: string | null;
  estimate_type: string | null;
  method: string | null;
  entry_mode: string | null;
}
