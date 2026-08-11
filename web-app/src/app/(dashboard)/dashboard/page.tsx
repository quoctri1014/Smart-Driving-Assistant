'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/Table';
import { sessionService, JourneySession } from '../../../services/sessionService';
import { violationService, Violation } from '../../../services/violationService';
import { Route, AlertOctagon, Car, Activity } from 'lucide-react';

export default function DashboardPage() {
  const [sessions, setSessions] = useState<JourneySession[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [sessData, violData] = await Promise.all([
          sessionService.getSessions(0, 5).catch(() => []),
          violationService.getViolations(0, 5).catch(() => [])
        ]);
        setSessions(sessData);
        setViolations(violData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-adas-text-primary">Overview</h1>
        <p className="text-adas-text-secondary mt-1">System status and recent activities</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-adas-primary/10 text-adas-primary flex items-center justify-center">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-adas-text-muted">Safety Score</p>
              <p className="text-2xl font-bold text-adas-text-primary">
                {/* FIX M: Not inventing Safety Score, using Placeholder until backend has it */}
                <span className="text-lg text-adas-text-secondary">Not Available</span>
              </p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-adas-success/10 text-adas-success flex items-center justify-center">
              <Route className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-adas-text-muted">Total Journeys</p>
              <p className="text-2xl font-bold text-adas-text-primary">
                {loading ? '-' : sessions.length > 0 ? `${sessions.length}+` : '0'}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-adas-danger/10 text-adas-danger flex items-center justify-center">
              <AlertOctagon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-adas-text-muted">Recent Violations</p>
              <p className="text-2xl font-bold text-adas-text-primary">
                {loading ? '-' : violations.length > 0 ? `${violations.length}+` : '0'}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-adas-warning/10 text-adas-warning flex items-center justify-center">
              <Car className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-adas-text-muted">Active Devices</p>
              <p className="text-2xl font-bold text-adas-text-primary">
                <span className="text-lg text-adas-text-secondary">Unknown</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Journeys</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 text-center text-adas-text-muted">Loading...</div>
            ) : sessions.length === 0 ? (
              <div className="p-6 text-center text-adas-text-muted">No recent journeys</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Start Time</TableHead>
                    <TableHead>Duration (min)</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions.map(s => (
                    <TableRow key={s.id}>
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

        <Card>
          <CardHeader>
            <CardTitle>Recent Violations</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 text-center text-adas-text-muted">Loading...</div>
            ) : violations.length === 0 ? (
              <div className="p-6 text-center text-adas-text-muted">No recent violations</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {violations.map(v => (
                    <TableRow key={v.id}>
                      <TableCell>
                        <Badge variant="danger" className="capitalize">{v.violation_type}</Badge>
                      </TableCell>
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
    </div>
  );
}
