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
import { Chart, registerables } from 'chart.js';
import { ApiService, TimeseriesRow, AggRow } from './api.service';

Chart.register(...registerables);

type Metric = 'ctr' | 'evpm';
type Dim = 'mm_dma' | 'site_id';

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
  selectedMetric: Metric = 'ctr';
  selectedDim: Dim = 'mm_dma';

  timeseriesData: TimeseriesRow[] = [];
  aggData: AggRow[] = [];
  aggDimKey = 'mm_dma';

  loading = false;

  private chart: Chart | null = null;
  private chartReady = false;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.api.getEventTypes().subscribe((types) => {
      this.eventTypes = types;
      this.selectedEvent = types[0] ?? '';
      this.loadAll();
    });
  }

  ngAfterViewInit(): void {
    this.chartReady = true;
    if (this.timeseriesData.length) {
      this.renderChart();
    }
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
  }

  onEventChange(): void {
    this.loadAll();
  }

  onMetricChange(m: Metric): void {
    this.selectedMetric = m;
    this.renderChart();
  }

  onDimChange(d: Dim): void {
    this.selectedDim = d;
    this.aggDimKey = d;
    this.loadAgg();
  }

  private loadAll(): void {
    this.loading = true;
    this.loadTimeseries();
    this.loadAgg();
  }

  private loadTimeseries(): void {
    this.api.getTimeseries(this.selectedEvent).subscribe((rows) => {
      this.timeseriesData = rows;
      this.loading = false;
      this.cdr.detectChanges();
      if (this.chartReady) {
        this.renderChart();
      }
    });
  }

  private loadAgg(): void {
    this.api
      .getAggregation(this.selectedDim, this.selectedEvent)
      .subscribe((rows) => {
        this.aggData = rows;
        this.aggDimKey = this.selectedDim;
        this.cdr.detectChanges();
      });
  }

  private renderChart(): void {
    if (!this.chartCanvas || !this.timeseriesData.length) return;

    const labels = this.timeseriesData.map((r) => r.date);
    const values = this.timeseriesData.map((r) =>
      this.selectedMetric === 'ctr' ? r.ctr : r.evpm
    );
    const label = this.selectedMetric === 'ctr' ? 'CTR (%)' : 'EvPM';
    const color = this.selectedMetric === 'ctr' ? '#6366f1' : '#10b981';

    this.chart?.destroy();
    this.chart = new Chart(this.chartCanvas.nativeElement, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label,
            data: values,
            borderColor: color,
            backgroundColor: color + '22',
            borderWidth: 2,
            pointRadius: 3,
            fill: true,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: 10, color: '#94a3b8' },
            grid: { color: '#1e293b' },
          },
          y: {
            ticks: { color: '#94a3b8' },
            grid: { color: '#1e293b' },
          },
        },
      },
    });
  }
}
