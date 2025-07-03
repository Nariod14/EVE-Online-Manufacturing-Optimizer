import React from "react";
import EditStationModal from "./EditStationModal";
import { http, HttpResponse } from 'msw';

export default {
  title: 'EditStationModal',
  component: EditStationModal,
  parameters: {
    msw: {
      handlers: [
        http.put('/api/stations/:id', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...body }, { status: 200 });
        }),
      ],
    },
  },
};

export const Default = () => (
  <EditStationModal
    open={true}
    onOpenChange={() => {}}
    station={{ id: 1, name: "Test Station", station_id: 123 }}
    onStationUpdate={() => alert("Updated!")}
  />
);
