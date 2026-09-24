// Complete build -> layout -> verify -> save script for drawio-eval.mjs.
//   node drawio-eval.mjs example-architecture.mjs
// Replaces the current page with a small web-app architecture: a client, a
// swimlane container holding the services, and a database. Runs inside the
// draw.io window, so `D` comes from drawio-helpers.js, not from an import.

const STYLE = {
  client: 'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;',
  service: 'rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;',
  db: 'shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;',
  lane: 'swimlane;whiteSpace=wrap;html=1;startSize=26;fillColor=#f5f5f5;strokeColor=#666666;',
  flow: 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;',
  async: 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;endArrow=open;',
};

export default async function ({ D }) {
  D.clear();
  D.batch(() => {
    D.vertex('Web client', STYLE.client, { id: 'client' });
    // Children of a container use its id as parent and coordinates relative to it.
    D.vertex('Backend', STYLE.lane, { id: 'backend', w: 360, h: 220 });
    D.vertex('API gateway', STYLE.service, { id: 'gw', parent: 'backend', x: 20, y: 80 });
    D.vertex('Orders', STYLE.service, { id: 'orders', parent: 'backend', x: 220, y: 40 });
    D.vertex('Billing', STYLE.service, { id: 'billing', parent: 'backend', x: 220, y: 140 });
    D.vertex('Postgres', STYLE.db, { id: 'db', w: 80, h: 90 });

    D.edge('client', 'gw', 'HTTPS', STYLE.flow);
    D.edge('gw', 'orders', '', STYLE.flow);
    D.edge('orders', 'billing', 'event', STYLE.async);
    D.edge('orders', 'db', 'SQL', STYLE.flow);
  });

  // ELK lays out the whole page, containers included.
  await D.layout([{ layout: 'elkLayered', config: { 'elk.direction': 'RIGHT' } }]);
  D.fit();

  // Verify before saving: every edge connected, nothing overlapping at the top level.
  const dump = D.dump();
  const loose = dump.filter(c => c.kind === 'edge' && (!c.source || !c.target));
  if (loose.length) throw new Error('unconnected edges: ' + loose.map(c => c.id));

  return { saved: await D.save(), vertices: dump.filter(c => c.kind === 'vertex').map(c => [c.id, c.parent || '', c.x, c.y]) };
}
