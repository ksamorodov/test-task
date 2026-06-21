import {
  Component,
  OnInit,
  OnDestroy,
  ElementRef,
  ViewChild,
  AfterViewInit,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';
import { ApiService, TimeseriesRow, AggRow } from './api.service';

Chart.register(...registerables);

type Dim = 'mm_dma' | 'site_id';

const CHART_COLORS = {
  ctr:  { border: '#6366f1', bg: '#6366f122' },
  evpm: { border: '#10b981', bg: '#10b98122' },
};

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartCanvas') chartCanvas!: ElementRef<HTMLCanvasElement>;

  eventTypes: string[] = [];
  selectedEvent = '';
  selectedDim: Dim = 'mm_dma';

  timeseriesData: TimeseriesRow[] = [];
  aggData: AggRow[] = [];
  aggDimKey: Dim = 'mm_dma';
  aggTotal = 0;
  aggOffset = 0;
  readonly aggLimit = 100;

  loading = false;
  error: string | null = null;

  private chart: Chart | null = null;
  private chartReady = false;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.api.getEventTypes().subscribe({
      next: (types) => {
        this.eventTypes = types;
        this.selectedEvent = types[0] ?? '';
        this.loadAll();
      },
      error: (e: HttpErrorResponse) => this.setError(e),
    });
  }

  ngAfterViewInit(): void {
    this.chartReady = true;
    if (this.timeseriesData.length) this.renderChart();
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
  }

  onEventChange(): void { this.loadAll(); }

  onDimChange(d: Dim): void {
    this.selectedDim = d;
    this.aggOffset = 0;
    this.loadAgg();
  }

  prevPage(): void {
    if (this.aggOffset === 0) return;
    this.aggOffset = Math.max(0, this.aggOffset - this.aggLimit);
    this.loadAgg();
  }

  nextPage(): void {
    if (this.aggOffset + this.aggLimit >= this.aggTotal) return;
    this.aggOffset += this.aggLimit;
    this.loadAgg();
  }

  get currentPage(): number { return Math.floor(this.aggOffset / this.aggLimit) + 1; }
  get totalPages(): number  { return Math.ceil(this.aggTotal / this.aggLimit); }

  private loadAll(): void {
    this.error = null;
    this.loading = true;
    this.aggOffset = 0;
    this.loadTimeseries();
    this.loadAgg();
  }

  private loadTimeseries(): void {
    this.api.getTimeseries(this.selectedEvent).subscribe({
      next: (rows) => {
        this.timeseriesData = rows;
        this.loading = false;
        this.cdr.detectChanges();
        if (this.chartReady) this.renderChart();
      },
      error: (e: HttpErrorResponse) => {
        this.loading = false;
        this.setError(e);
      },
    });
  }

  private loadAgg(): void {
    this.api
      .getAggregation(this.selectedDim, this.selectedEvent, this.aggLimit, this.aggOffset)
      .subscribe({
        next: (res) => {
          this.aggData = res.items;
          this.aggTotal = res.total;
          this.aggDimKey = this.selectedDim;
          this.cdr.detectChanges();
        },
        error: (e: HttpErrorResponse) => this.setError(e),
      });
  }

  private setError(e: HttpErrorResponse): void {
    this.error = e.status === 0
      ? 'Не удалось подключиться к серверу. Убедитесь, что backend запущен на порту 8000.'
      : `Ошибка сервера: ${e.status} ${e.statusText}`;
    this.cdr.detectChanges();
  }

  // ── Chart ────────────────────────────────────────────────────────────────

  private renderChart(): void {
    if (!this.chartCanvas || !this.timeseriesData.length) return;

    const labels = this.timeseriesData.map((r) => r.date);

    this.chart?.destroy();
    this.chart = new Chart(this.chartCanvas.nativeElement, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'CTR (%)',
            data: this.timeseriesData.map((r) => r.ctr),
            borderColor: CHART_COLORS.ctr.border,
            backgroundColor: CHART_COLORS.ctr.bg,
            borderWidth: 2,
            pointRadius: 3,
            fill: true,
            tension: 0.3,
            yAxisID: 'yCtr',
          },
          {
            label: 'EvPM',
            data: this.timeseriesData.map((r) => r.evpm),
            borderColor: CHART_COLORS.evpm.border,
            backgroundColor: CHART_COLORS.evpm.bg,
            borderWidth: 2,
            pointRadius: 3,
            fill: true,
            tension: 0.3,
            yAxisID: 'yEvpm',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: true,
            labels: { color: '#94a3b8', boxWidth: 12 },
          },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: 10, color: '#94a3b8' },
            grid: { color: '#1e293b' },
          },
          yCtr: {
            type: 'linear',
            position: 'left',
            ticks: { color: CHART_COLORS.ctr.border },
            grid: { color: '#1e293b' },
            title: { display: true, text: 'CTR (%)', color: CHART_COLORS.ctr.border },
          },
          yEvpm: {
            type: 'linear',
            position: 'right',
            ticks: { color: CHART_COLORS.evpm.border },
            grid: { drawOnChartArea: false },
            title: { display: true, text: 'EvPM', color: CHART_COLORS.evpm.border },
          },
        },
      },
    });
  }
}
