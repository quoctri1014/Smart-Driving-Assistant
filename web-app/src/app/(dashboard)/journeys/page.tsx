'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/Table';
import { sessionService, JourneySession } from '../../../services/sessionService';

export default function JourneysPage() {
  const [sessions, setSessions] = useState<JourneySession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    sessionService.getSessions(0, 100)
      .then(setSessions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-adas-text-primary">Journeys</h1>
        <p className="text-adas-text-secondary mt-1">Driving session history</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Journeys</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 text-center text-adas-text-muted">Loading...</div>
          ) : sessions.length === 0 ? (
            <div className="p-6 text-center text-adas-text-muted">No journeys found</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Session ID</TableHead>
                  <TableHead>Driver ID</TableHead>
                  <TableHead>Start Time</TableHead>
                  <TableHead>Duration (min)</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map(s => (
                  <TableRow key={s.id}>
                    <TableCell>#{s.id}</TableCell>
                    <TableCell>Dr. {s.driver_id}</TableCell>
                    <TableCell>{new Date(s.start_time).toLocaleString()}</TableCell>
                    <TableCell>{s.total_minutes ? Math.round(s.total_minutes) : '-'}</TableCell>
                    <TableCell>
                      {s.end_time ? <Badge variant="success">Completed</Badge> : <Badge variant="warning">In Progress</Badge>}
                    </TableCell>
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
