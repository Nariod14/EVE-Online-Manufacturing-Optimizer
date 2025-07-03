import { http, HttpResponse } from 'msw';
import { Blueprint, BlueprintT1, BlueprintT2, mockBlueprints } from '@/types/blueprints';
import { Material, mockMaterials } from '@/types/materials';
import { mockStations } from '@/types/stations';
import { mockOptimizeResponse } from '@/types/optimize';
let localStations = [...mockStations];
let localMaterials = [...mockMaterials];

const localOptimizeResponse = mockOptimizeResponse;

interface BlueprintPayload {
  blueprint_paste: string;
  invention_materials: string;
  amt_per_run: number;
  sell_price: number;
  material_cost: number;
  tier: string;
  invention_chance: number;
  runs_per_copy: number;
}

let localBlueprints: Blueprint[] = [...mockBlueprints];
let nextId = mockBlueprints.length + 1;

// Simple in-memory login state
let isLoggedIn = false;

export const handlers = [
 // Simulate EVE login redirect flow
   http.get('/login', () => {
     console.log("🔐 MSW Intercepted /login");
     // Simulate redirect to EVE OAuth (but we skip the real OAuth)
     isLoggedIn = true;
     return HttpResponse.redirect('/callback'); // mock OAuth provider redirecting back
   }),

  // Simulate OAuth callback
  http.get('/callback', () => {
    console.log('🔐 MSW Intercepted /callback');

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('isLoggedIn', 'true');
    }

    return new Response(null, { status: 302, headers: { Location: '/' } });
  }),


   // Auth status
  http.get('/auth/status', () => {
    const loggedIn = typeof window !== 'undefined' && localStorage.getItem('isLoggedIn') === 'true';

    console.log('MSW /auth/status, loggedIn:', loggedIn);

    return new Response(JSON.stringify({
      character_name: loggedIn ? 'Nariod Naren' : undefined,
      logged_in: loggedIn,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }),



   // Logout
  http.post('/logout', () => {
    console.log('🔓 MSW Intercepted /logout');
    localStorage.removeItem('isLoggedIn'); // Clear dev mock storage
    return new Response(null, { status: 200 });
  }),

  http.post('/api/materials/update_materials', async ({ request }) => {
    console.log('📦 MSW Intercepted /api/materials/update_materials');

    try {
      const body = await request.json() as {
        materials: Record<string, number>;
        updateType: 'add' | 'replace';
      };

      const { materials, updateType } = body;

      const nextId = (() => {
        const ids = localMaterials.map(m => m.id);
        return ids.length ? Math.max(...ids) + 1 : 1;
      })();

      if (updateType === 'replace') {
        console.log('🔁 Replacing all materials');

        localMaterials = Object.entries(materials).map(([name, quantity], idx) => ({
          id: nextId + idx,
          name,
          quantity,
          sell_price: null,
          type_id: null,
          category: null,
        }));
      } else if (updateType === 'add') {
        console.log('➕ Adding/updating materials');

        const materialMap = new Map(localMaterials.map((m) => [m.name, m]));

        for (const [name, quantity] of Object.entries(materials)) {
          const existing = materialMap.get(name);
          if (existing) {
            existing.quantity = quantity;
          } else {
            materialMap.set(name, {
              id: nextId + materialMap.size,
              name,
              quantity,
              sell_price: null,
              type_id: null,
              category: null,
            });
          }
        }

        localMaterials = Array.from(materialMap.values());
      }

      console.log('✅ Materials updated:', localMaterials);
      return HttpResponse.json({ message: 'Materials updated successfully' }, { status: 200 });

    } catch (err) {
      console.error('❌ Error parsing update_materials request:', err);
      return HttpResponse.json({ error: 'Invalid request' }, { status: 400 });
    }
  }),


 
  // GET /api/stations
  http.get('/api/stations', () => {
    console.log("🛰️ MSW Intercepted /api/stations");
    return HttpResponse.json(localStations);
  }),
  // POST /api/stations
  http.post('/api/stations', async ({
    request
  }) => {
    const body = await request.json() as {
      name: string;
      station_id: number;
    };
    const newStation = {
      id: Date.now(),
      ...body,
      blueprints: []
    };
    localStations.push(newStation);
    return HttpResponse.json(newStation, {
      status: 201
    });
  }),
  // PUT /api/stations/:id
  http.put('/api/stations/:id', async ({
    params,
    request
  }) => {
    const {
      id
    } = params;
    const body = await request.json() as {
      name: string;
      station_id: number;
    };
    localStations = localStations.map(s => s.id === Number(id) ? {
      ...s,
      ...body
    } : s);
    return HttpResponse.json({
      success: true
    });
  }),
  // DELETE /api/stations/:id
  http.delete('/api/stations/:id', ({
    params
  }) => {
    const {
      id
    } = params;
    localStations = localStations.filter(s => s.id !== Number(id));
    return HttpResponse.json({
      success: true
    });
  }),
  // GET blueprints
  http.get("/api/blueprints/blueprints", ({ request }) => {
    console.log("[MSW] GET /blueprints ->", localBlueprints);
    return HttpResponse.json(localBlueprints);
  }),

  // PUT update blueprint
  http.put("/api/blueprints/blueprint/:id", async ({ request, params }) => {
    const blueprintId = parseInt(params.id as string);
    const body = await request.json() as { [key: string]: any};

    console.log("Before update:", JSON.stringify(localBlueprints, null, 2));

    localBlueprints = localBlueprints.map((bp) =>
      bp.id === blueprintId
        ? {
            ...bp,
            ...body,
            materials: body.materials ?? bp.materials,
          }
        : bp
    );

    console.log("After update:", JSON.stringify(localBlueprints, null, 2));

    return HttpResponse.json({ success: true });
  }),


  // DELETE blueprint
  http.delete("/api/blueprints/blueprint/:id", ({ params }) => {
    const blueprintId = parseInt(params.id as string);
    console.log(`Mock delete blueprint ${blueprintId}`);

    localBlueprints = localBlueprints.filter((bp) => bp.id !== blueprintId);

    return HttpResponse.json({ success: true });
  }),

  // POST reset max values
  http.post("/api/blueprints/blueprints/reset_max", () => {
    console.log("Mock reset all blueprint max values");

    localBlueprints = localBlueprints.map((bp) => ({
      ...bp,
      max: null,
    }));

    return HttpResponse.json({ success: true });
  }),

  http.get('/api/materials/materials', () => {
    console.log("🛰️ MSW Intercepted /api/materials/materials");
    return HttpResponse.json(localMaterials);
  }),

  // GET single material by ID
  http.get("/api/materials/material/:id", ({ params }) => {
    const id = Number(params.id);
    const material = localMaterials.find((m) => m.id === id);

    if (!material) {
      return new HttpResponse("Material not found", { status: 404 });
    }

    return HttpResponse.json(material);
  }),

  // POST update material info (simulated)
  http.put("/api/materials/material/:id", async ({ request, params }) => {
    const id = Number(params.id);
    const updatedMaterial = await request.json() as Partial<Material>;

    const index = localMaterials.findIndex((mat) => mat.id === id);
    if (index === -1) {
      console.warn(`🛰️ Material with id ${id} not found for update`);
      return new HttpResponse("Material not found", { status: 404 });
    }

    localMaterials = localMaterials.map((mat) =>
      mat.id === id ? { ...mat, ...updatedMaterial, id } : mat
    );

    console.log(`🛰️ Updated Material ${id}:`, localMaterials[index]);
    return HttpResponse.json(localMaterials[index]);
  }),

  // DELETE material
  http.delete("/api/materials/material/:id", ({ params }) => {
    const id = Number(params.id);
    const index = localMaterials.findIndex((m) => m.id === id);
    if (index === -1) {
      return new HttpResponse("Material not found", { status: 404 });
    }

    const deleted = localMaterials.splice(index, 1)[0];
    console.log(`🛰️ MSW Deleted Material ${id}`);
    return HttpResponse.json(deleted);
  }),

  // POST to add a new material
  http.post("/api/materials/material", async ({ request }) => {
    const newMaterial = await request.json() as Material;

    const newId = localMaterials.length > 0 ? Math.max(...localMaterials.map((m) => m.id)) + 1 : 1;
    const created = { ...newMaterial, id: newId };

    localMaterials.push(created);

    console.log(`🛰️ MSW Created Material ${newId}:`, created);
    return HttpResponse.json(created);
  }),


  // GET /api/blueprints/optimize
  http.get('/api/blueprints/optimize', () => {
    console.log("🧠 MSW Intercepted /api/blueprints/optimize");
    return HttpResponse.json(localOptimizeResponse);
  }),

  // POST /api/blueprints/blueprints to add a new blueprint by the parser
  http.post('/api/blueprints/blueprints', async ({ request }) => {
    console.log('📦 MSW Intercepted POST /api/blueprints/blueprints');

    const body = await request.json() as BlueprintPayload;

    const {
      blueprint_paste,
      invention_materials,
      sell_price,
      amt_per_run,
      material_cost,
      tier,
      invention_chance,
      runs_per_copy,
    } = body;

    // Parse name and type ID from blueprint_paste first line
    const [firstLine] = blueprint_paste.trim().split('\n');
    const [nameRaw, typeIdRaw] = firstLine.split('\t');
    const name = nameRaw.replace(' Blueprint', '').trim();
    const type_id = parseInt(typeIdRaw?.trim() || '0');

    if (!name || isNaN(type_id)) {
      return HttpResponse.json({ error: 'Invalid blueprint format' }, { status: 400 });
    }

    // Use a copy or a slice of mockMaterials for this blueprint
    // Optionally, you can customize or filter mockMaterials based on input
    const materialsForBlueprint = [...mockMaterials];

    let newBlueprint: Blueprint;

    if (tier === 'T2') {
      newBlueprint = {
        id: nextId++,
        name,
        type_id,
        amt_per_run: amt_per_run ?? 1,
        runs_per_copy: runs_per_copy ?? 10,
        materials: materialsForBlueprint,
        sell_price: sell_price ?? 0,
        material_cost: material_cost ?? 0,
        full_material_cost: 0,
        invention_cost: 0,
        invention_chance: invention_chance ?? 0,
        tier: 'T2',
        region_id: 0,
        use_jita_sell: false,
        used_jita_fallback: false,
      } satisfies BlueprintT2;
    } else {
      newBlueprint = {
        id: nextId++,
        name,
        type_id,
        amt_per_run: amt_per_run ?? 1,
        materials: materialsForBlueprint,
        sell_price: sell_price ?? 0,
        material_cost: material_cost ?? 0,
        tier: 'T1',
        region_id: 0,
        use_jita_sell: false,
        used_jita_fallback: false,
      } satisfies BlueprintT1;
    }

    localBlueprints.push(newBlueprint);

    return HttpResponse.json({ message: 'Blueprint added successfully' }, { status: 201 });
  })

];
