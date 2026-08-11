'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/Table';
import { violationService, Violation } from '../../../services/violationService';

export default function ViolationsPage() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    violationService.getViolations(0, 100)
      .then(setViolations)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-adas-text-primary">Violations</h1>
        <p className="text-adas-text-secondary mt-1">Logged traffic and driver violations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Violations</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 text-center text-adas-text-muted">Loading...</div>
          ) : violations.length === 0 ? (
            <div className="p-6 text-center text-adas-text-muted">No violations found</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Driver ID</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {violations.map(v => (
                  <TableRow key={v.id}>
                    <TableCell>#{v.id}</TableCell>
                    <TableCell>
                      <Badge variant="danger" className="capitalize">{v.violation_type}</Badge>
                    </TableCell>
                    <TableCell>Dr. {v.driver_id}</TableCell>
                    <TableCell>{new Date(v.timestamp).toLocaleString()}</TableCell>
                    <TableCell>{Math.round(v.confidence * 100)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
