'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { Badge } from './Badge';
import { AlertBanner } from './AlertBanner';

export default function GenericDataPage({ title, description, unavailable = false }: { title: string, description: string, unavailable?: boolean }) {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-adas-text-primary">{title}</h1>
        <p className="text-adas-text-secondary mt-1">{description}</p>
      </div>

      {unavailable ? (
        <AlertBanner variant="warning" title="Data Unavailable">
          The backend API does not currently expose full data for this section.
        </AlertBanner>
      ) : (
        <Card>
          <CardContent className="p-6 text-center text-adas-text-muted">
            Work in progress. This page will connect to the real API endpoints once detailed endpoints are available.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
