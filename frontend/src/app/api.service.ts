import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const BASE = 'http://localhost:8000/api';

export interface TimeseriesRow {
  date: string;
  impressions: number;
  events: number;
  ctr: number;
  evpm: number;
}

export interface AggRow {
  [key: string]: string | number;
  impressions: number;
  events: number;
  ctr: number;
  evpm: number;
}

export interface PaginatedAggregation {
  total: number;
  limit: number;
  offset: number;
  items: AggRow[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  getEventTypes(): Observable<string[]> {
    return this.http.get<string[]>(`${BASE}/event-types`);
  }

  getTimeseries(event: string): Observable<TimeseriesRow[]> {
    return this.http.get<TimeseriesRow[]>(`${BASE}/timeseries`, { params: { event } });
  }

  getAggregation(
    by: string,
    event: string,
    limit = 100,
    offset = 0,
  ): Observable<PaginatedAggregation> {
    return this.http.get<PaginatedAggregation>(`${BASE}/aggregation`, {
      params: { by, event, limit, offset },
    });
  }
}
