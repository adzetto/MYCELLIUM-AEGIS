/* =============================================================================
   MYCELLIUM-AEGIS · SAYISAL İKİZ
   scene.js — Fiziksel tabanlı (PBR) üç boyutlu sahne
   -----------------------------------------------------------------------------
   İki görünüm, tek WebGL bağlamı:
     KESİT  1 birim = 10 cm → toprak profili kesiti, miselyum ağı, gömülü donanım
     SAHA   1 birim = 1 m   → orman parseli, düğümler, kule, LoRa bağlantıları

   Gerçekçilik: yordamsal albedo/normal/pürüzlülük haritaları (textures.js),
   PMREM ile ortam aydınlatması, PCF yumuşak gölgeler, ACES ton eşlemesi.
   ============================================================================= */
(function (global) {
  'use strict';

  const T = global.THREE;
  const TX = global.AEGIS_TEX;
  const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
  const rnd = (a, b) => a + Math.random() * (b - a);

  /* ------------------------------------------------------------- gürültü -- */
  function hash2(x, y) { const h = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return h - Math.floor(h); }
  function vnoise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash2(xi, yi), b = hash2(xi + 1, yi), c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1);
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v;
  }
  function fbm(x, y) { let s = 0, a = 0.5, f = 1; for (let i = 0; i < 4; i++) { s += a * vnoise(x * f, y * f); f *= 2.07; a *= 0.5; } return s; }
  const terrainH = (x, z) => (fbm(x * 0.012 + 11, z * 0.012 + 7) - 0.5) * 26 + (fbm(x * 0.05, z * 0.05) - 0.5) * 3;

  /* -------------------------------------------- yuvarlatılmış kutu gövde -- */
  function roundedBox(w, h, d, r, seg) {
    const shape = new T.Shape();
    const x = -w / 2, y = -h / 2;
    shape.moveTo(x + r, y);
    shape.lineTo(x + w - r, y); shape.quadraticCurveTo(x + w, y, x + w, y + r);
    shape.lineTo(x + w, y + h - r); shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    shape.lineTo(x + r, y + h); shape.quadraticCurveTo(x, y + h, x, y + h - r);
    shape.lineTo(x, y + r); shape.quadraticCurveTo(x, y, x + r, y);
    const dep = Math.max(0.01, d - r * 0.6);
    const g = new T.ExtrudeGeometry(shape, {
      depth: dep, bevelEnabled: true, bevelThickness: r * 0.3,
      bevelSize: r * 0.3, bevelSegments: seg || 3, curveSegments: seg || 6
    });
    g.translate(0, 0, -dep / 2);
    g.computeVertexNormals();
    return g;
  }

  /* -------------------------------------------------------- yazı etiketi -- */
  /* Beyaz tema · Computer Modern serif                                        */
  function makeLabel(text, opt) {
    opt = Object.assign({ size: 46, color: '#12171c', bg: 'rgba(255,255,255,.97)',
      pad: 18, border: '#98a1a8', scale: 1 }, opt);
    const c = document.createElement('canvas'), x = c.getContext('2d');
    const font = `${opt.size}px "CMU Serif", Georgia, serif`;
    x.font = font;
    const w = Math.ceil(x.measureText(text).width) + opt.pad * 2;
    const h = Math.round(opt.size * 1.62);
    c.width = w; c.height = h;
    x.font = font; x.textBaseline = 'middle';
    if (opt.bg) {
      x.fillStyle = opt.bg;
      x.beginPath(); x.roundRect(1, 1, w - 2, h - 2, 5); x.fill();
      if (opt.border) { x.strokeStyle = opt.border; x.lineWidth = 1.6; x.stroke(); }
    }
    x.fillStyle = opt.color;
    x.fillText(text, opt.pad, h / 2 + 1);
    const tex = new T.CanvasTexture(c);
    tex.colorSpace = T.SRGBColorSpace; tex.anisotropy = 8;
    const spr = new T.Sprite(new T.SpriteMaterial({ map: tex, transparent: true,
      depthTest: opt.depthTest !== false, depthWrite: false, sizeAttenuation: true,
      toneMapped: false, fog: false }));
    spr.userData.aspect = w / h;
    spr.scale.set((w / h) * opt.scale, opt.scale, 1);
    return spr;
  }

  /* ========================================================================= */
  const S = { ready: false, mode: 'micro', view: 'sub', hot: [], growth: 1 };
  let renderer, scene, camera, sun, hemi, fill, fireLight, pmrem, envRT, dotTex;
  let macro, micro;
  const cam = { pos: new T.Vector3(), tgt: new T.Vector3(), posT: new T.Vector3(), tgtT: new T.Vector3(), fovT: 38 };
  const orbit = { a: 0, a0: 0, speed: 0.1, sweep: 0.3, radius: 20, baseY: 4, drag: false, px: 0, py: 0, userA: 0, userB: 0 };

  const MX = 26, MZ = 15, CUT = 6.5;

  const VIEWS = {
    sub:   { mode: 'micro', pos: [15, 8.5, 40],   tgt: [0, -3.4, 1.0],   fov: 34, orbit: 0.09, sweep: 0.16 },
    node:  { mode: 'micro', pos: [3.6, -0.2, 10], tgt: [0.5, -1.7, 2.3], fov: 34, orbit: 0.10, sweep: 0.20 },
    strata:{ mode: 'micro', pos: [2.5, 0.5, 33],  tgt: [0, -3.6, 1.0],   fov: 30, orbit: 0.07, sweep: 0.12 },
    site:  { mode: 'macro', pos: [96, 62, 108],   tgt: [0, 8, -6],       fov: 36, orbit: 0.018, sweep: 0 },
    tower: { mode: 'macro', pos: [24, 20, 32],    tgt: [0, 14, 0],       fov: 34, orbit: 0.026, sweep: 0 }
  };

  /* ======================================================== KESİT DÜNYASI = */
  let layerMeshes = [], hyphaGeo, hyphaLine, hyphaPaths = [], pulses = [], pulsePts;
  let nodeGrp, surfGrp, cableFlow = [], safeBand, electrodeTips = [];

  function buildMicro() {
    micro = new T.Group(); scene.add(micro);

    const palettes = [
      { base: [0x4a, 0x3c, 0x2c], seed: 3,  grain: 0.50, organic: 0.50, pebbles: 12, roughBase: 0.97 },
      { base: [0x5c, 0x46, 0x30], seed: 11, grain: 0.46, organic: 0.42, pebbles: 18, roughBase: 0.96 },
      { base: [0x6d, 0x53, 0x36], seed: 19, grain: 0.42, organic: 0.30, pebbles: 26, roughBase: 0.95 },
      { base: [0x7b, 0x5e, 0x3c], seed: 27, grain: 0.38, organic: 0.22, pebbles: 30, roughBase: 0.94 },
      { base: [0x88, 0x69, 0x44], seed: 35, grain: 0.34, organic: 0.16, pebbles: 34, roughBase: 0.93 },
      { base: [0x7f, 0x64, 0x42], seed: 43, grain: 0.30, organic: 0.12, pebbles: 30, roughBase: 0.93 },
      { base: [0x6f, 0x5c, 0x42], seed: 51, grain: 0.26, organic: 0.08, pebbles: 22, roughBase: 0.92 }
    ];

    AEGIS_DATA.soilLayers.forEach((L, i) => {
      const h = (L.z1 - L.z0) * 10;
      const t = TX.soil(palettes[Math.min(i, palettes.length - 1)]);
      const rep = [1.5, Math.max(0.3, h / 4.2)];
      t.map.repeat.set(rep[0], rep[1]);
      t.normalMap.repeat.set(rep[0], rep[1]);
      t.roughnessMap.repeat.set(rep[0], rep[1]);
      const mat = new T.MeshStandardMaterial({
        map: t.map, normalMap: t.normalMap, roughnessMap: t.roughnessMap,
        normalScale: new T.Vector2(1.15, 1.15), roughness: 1, metalness: 0
      });
      const m = new T.Mesh(new T.BoxGeometry(MX, h, MZ), mat);
      m.position.set(0, -(L.z0 * 10 + h / 2), -MZ / 2);
      m.castShadow = true; m.receiveShadow = true;
      m.userData = { layer: L, hotspot: 'layer:' + L.z0 };
      micro.add(m); layerMeshes.push(m); S.hot.push(m);

      if (i > 0) {
        const e = new T.Mesh(new T.BoxGeometry(MX + 0.02, 0.03, 0.05),
          new T.MeshBasicMaterial({ color: 0x2b2118, transparent: true, opacity: 0.4 }));
        e.position.set(0, -L.z0 * 10, 0.02); micro.add(e);
      }
    });

    /* --- yüzey örtüsü --- */
    const lt = TX.litter(33);
    lt.map.repeat.set(3, 2); lt.normalMap.repeat.set(3, 2);
    const litter = new T.Mesh(new T.BoxGeometry(MX + 0.04, 0.4, MZ + 0.04),
      new T.MeshStandardMaterial({ map: lt.map, normalMap: lt.normalMap,
        normalScale: new T.Vector2(1.3, 1.3), roughness: 0.98, metalness: 0 }));
    litter.position.set(0, 0.18, -MZ / 2);
    litter.castShadow = true; litter.receiveShadow = true;
    micro.add(litter);

    /* --- çim --- */
    const gN = 2600;
    const bladeG = new T.PlaneGeometry(0.045, 0.52, 1, 3);
    bladeG.translate(0, 0.26, 0);
    const bp = bladeG.attributes.position;
    for (let i = 0; i < bp.count; i++) bp.setZ(i, Math.pow(bp.getY(i) / 0.52, 2) * 0.13);
    bladeG.computeVertexNormals();
    const blades = new T.InstancedMesh(bladeG, new T.MeshStandardMaterial({
      color: 0xffffff, roughness: 0.84, metalness: 0, side: T.DoubleSide }), gN);
    blades.castShadow = true;
    const m4 = new T.Matrix4(), qq = new T.Quaternion(), s3 = new T.Vector3(), p3 = new T.Vector3();
    const cA = new T.Color(0x4d6a2c), cB = new T.Color(0x9aa85c);
    for (let i = 0; i < gN; i++) {
      p3.set(rnd(-MX / 2, MX / 2), 0.33, rnd(-MZ + 0.2, -0.12));
      qq.setFromEuler(new T.Euler(rnd(-0.18, 0.18), rnd(0, 6.28), rnd(-0.22, 0.22)));
      const s = rnd(0.5, 1.5); s3.set(rnd(0.8, 1.3), s, 1);
      m4.compose(p3, qq, s3); blades.setMatrixAt(i, m4);
      blades.setColorAt(i, cA.clone().lerp(cB, Math.pow(Math.random(), 1.4)));
    }
    blades.instanceMatrix.needsUpdate = true;
    if (blades.instanceColor) blades.instanceColor.needsUpdate = true;
    micro.add(blades);

    /* --- kaldırılmış toprağın sınırı: yalnızca ince bir kesit çerçevesi --- */
    const frameG = new T.BufferGeometry().setFromPoints([
      new T.Vector3(-MX / 2, 0.37, CUT), new T.Vector3(MX / 2, 0.37, CUT),
      new T.Vector3(-MX / 2, 0.37, CUT), new T.Vector3(-MX / 2, 0.37, 0),
      new T.Vector3(MX / 2, 0.37, CUT), new T.Vector3(MX / 2, 0.37, 0)
    ]);
    micro.add(new T.LineSegments(frameG, new T.LineBasicMaterial({
      color: 0x6f6252, transparent: true, opacity: 0.30 })));

    /* --- güvenli bölge --- */
    safeBand = new T.Mesh(new T.BoxGeometry(MX + 0.1, 0.5, MZ + CUT + 0.1),
      new T.MeshBasicMaterial({ color: 0x1a7f5a, transparent: true, opacity: 0.1, depthWrite: false }));
    safeBand.position.set(0, -1.75, (CUT - MZ) / 2); micro.add(safeBand);

    /* --- derinlik cetveli --- */
    [0, 5, 10, 15, 20, 40, 60].forEach((cm) => {
      const y = -cm / 10;
      micro.add(new T.Line(new T.BufferGeometry().setFromPoints([
        new T.Vector3(-MX / 2 - 0.15, y, CUT * 0.5), new T.Vector3(-MX / 2 - 1.5, y, CUT * 0.5)]),
        new T.LineBasicMaterial({ color: 0x33403a, transparent: true, opacity: 0.85 })));
      const lb = makeLabel(cm + ' cm', { scale: 0.44, size: 40, bg: 'rgba(255,255,255,.84)', border: null });
      lb.position.set(-MX / 2 - 2.6, y, CUT * 0.5); micro.add(lb);
    });
    const safeLbl = makeLabel('15–20 cm  güvenli bölge', { scale: 0.46, size: 40, color: '#0d5c42', border: '#1a7f5a' });
    safeLbl.position.set(MX / 2 + 4.0, -1.75, CUT * 0.5); micro.add(safeLbl);

    const base = new T.Mesh(new T.BoxGeometry(MX - 0.02, 0.3, MZ - 0.02),
      new T.MeshStandardMaterial({ color: 0x574a3a, roughness: 1, metalness: 0 }));
    base.position.set(0, -8.95, -MZ / 2); base.receiveShadow = true; micro.add(base);

    buildHyphae();
    buildNode();
  }

  /* ------------------------------------------------------- miselyum ağı --- */
  function buildHyphae() {
    const verts = [], cols = [];
    const c0 = new T.Color(0x14603f), c1 = new T.Color(0xa8e6cd);
    for (let r = 0; r < 52; r++) {
      const start = new T.Vector3(rnd(-MX / 2 + 1, MX / 2 - 1), rnd(-2.8, -0.9), rnd(0.4, CUT - 0.4));
      grow(start, new T.Vector3(rnd(-1, 1), rnd(-0.25, 0.25), rnd(-1, 1)).normalize(), 0, verts, cols, c0, c1);
    }
    hyphaGeo = new T.BufferGeometry();
    hyphaGeo.setAttribute('position', new T.Float32BufferAttribute(verts, 3));
    hyphaGeo.setAttribute('color', new T.Float32BufferAttribute(cols, 3));
    hyphaLine = new T.LineSegments(hyphaGeo, new T.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.8, depthWrite: false }));
    hyphaGeo.setDrawRange(0, verts.length / 3);
    micro.add(hyphaLine);

    const P = 80, pp = new Float32Array(P * 3);
    for (let i = 0; i < P; i++)
      pulses.push({ path: hyphaPaths[(Math.random() * hyphaPaths.length) | 0], u: Math.random(), speed: rnd(0.12, 0.4) });
    const pg = new T.BufferGeometry();
    pg.setAttribute('position', new T.BufferAttribute(pp, 3));
    pulsePts = new T.Points(pg, new T.PointsMaterial({ size: 0.4, map: dotTex, color: 0x0f6b4a,
      transparent: true, opacity: 0.95, depthWrite: false, sizeAttenuation: true }));
    micro.add(pulsePts);
  }
  function grow(p, dir, depth, verts, cols, c0, c1) {
    if (depth > 3) return;
    const path = [p.clone()];
    let cur = p.clone(); const d = dir.clone();
    for (let i = 0, n = (14 - depth * 3) | 0; i < n; i++) {
      d.x += rnd(-0.5, 0.5); d.y += rnd(-0.28, 0.22); d.z += rnd(-0.5, 0.5); d.normalize();
      const nx = cur.clone().addScaledVector(d, rnd(0.35, 0.85) * (1 - depth * 0.15));
      nx.y = clamp(nx.y, -3.6, -0.55);
      nx.x = clamp(nx.x, -MX / 2 + 0.4, MX / 2 - 0.4);
      nx.z = clamp(nx.z, 0.25, CUT - 0.25);
      const t0 = clamp((cur.y + 3.6) / 3.05, 0, 1), t1 = clamp((nx.y + 3.6) / 3.05, 0, 1);
      const ca = c0.clone().lerp(c1, t0 * 0.7), cb = c0.clone().lerp(c1, t1 * 0.7);
      verts.push(cur.x, cur.y, cur.z, nx.x, nx.y, nx.z);
      cols.push(ca.r, ca.g, ca.b, cb.r, cb.g, cb.b);
      path.push(nx.clone());
      if (Math.random() < 0.2 && depth < 3)
        grow(nx, new T.Vector3(rnd(-1, 1), rnd(-0.3, 0.3), rnd(-1, 1)).normalize(), depth + 1, verts, cols, c0, c1);
      cur = nx;
    }
    if (path.length > 3) hyphaPaths.push(new T.CatmullRomCurve3(path));
  }

  /* ------------------------------------------------- gömülü donanım ------- */
  function buildNode() {
    nodeGrp = new T.Group(); nodeGrp.position.set(0.4, -1.8, 2.3); micro.add(nodeGrp);

    const bc = TX.biocomposite();
    const shell = new T.Mesh(roundedBox(2.6, 1.2, 1.8, 0.14, 4), new T.MeshPhysicalMaterial({
      map: bc.map, normalMap: bc.normalMap, normalScale: new T.Vector2(0.9, 0.9),
      roughness: 0.86, metalness: 0, transparent: true, opacity: 0.17,
      side: T.DoubleSide, depthWrite: false, clearcoat: 0.14, clearcoatRoughness: 0.7 }));
    shell.userData.hotspot = 'node'; shell.castShadow = true;
    nodeGrp.add(shell); S.hot.push(shell);
    nodeGrp.add(new T.LineSegments(new T.EdgesGeometry(roundedBox(2.6, 1.2, 1.8, 0.14, 2)),
      new T.LineBasicMaterial({ color: 0x6d5c3f, transparent: true, opacity: 0.55 })));

    const pt = TX.pcb();
    const pcbM = new T.Mesh(new T.BoxGeometry(2.15, 0.055, 1.35),
      new T.MeshStandardMaterial({ map: pt.map, roughness: 0.5, metalness: 0.08 }));
    pcbM.position.y = 0.06; pcbM.castShadow = true; pcbM.receiveShadow = true;
    nodeGrp.add(pcbM);

    const chipMat = new T.MeshPhysicalMaterial({ color: 0x181a1e, roughness: 0.44, metalness: 0.12,
      clearcoat: 0.5, clearcoatRoughness: 0.35 });
    const pinMat = new T.MeshStandardMaterial({ color: 0xc9cdd2, roughness: 0.28, metalness: 0.95 });
    [
      { id: 'opa333',  x: -0.74, z: -0.30, w: 0.30, h: 0.10, pins: 4 },
      { id: 'ads1115', x: -0.20, z: -0.30, w: 0.34, h: 0.11, pins: 5 },
      { id: 'stm32l4', x:  0.44, z: -0.18, w: 0.52, h: 0.13, pins: 8 },
      { id: 'max3485', x:  0.88, z:  0.36, w: 0.28, h: 0.10, pins: 4 },
      { id: 'bme280',  x: -0.66, z:  0.38, w: 0.20, h: 0.09, pins: 0 }
    ].forEach(ch => {
      const g = new T.Group(); g.position.set(ch.x, 0.09, ch.z);
      const body = new T.Mesh(roundedBox(ch.w, ch.w * 0.86, ch.h, 0.012, 2), chipMat);
      body.position.y = ch.h / 2; body.rotation.x = -Math.PI / 2;
      body.castShadow = true; body.userData.hotspot = ch.id;
      g.add(body); S.hot.push(body);
      for (let s = 0; s < ch.pins; s++) {
        const t = (s + 0.5) / ch.pins - 0.5;
        [-1, 1].forEach(sd => {
          const pin = new T.Mesh(new T.BoxGeometry(ch.w / (ch.pins * 2.6), 0.016, 0.05), pinMat);
          pin.position.set(t * ch.w * 0.86, 0.012, sd * (ch.w * 0.47));
          g.add(pin);
        });
      }
      g.userData.hotspot = ch.id;
      nodeGrp.add(g);
    });
    const passM = new T.MeshStandardMaterial({ color: 0xb9a67c, roughness: 0.55, metalness: 0.2 });
    for (let i = 0; i < 26; i++) {
      const p = new T.Mesh(new T.BoxGeometry(0.055, 0.028, 0.03), passM);
      p.position.set(rnd(-0.95, 0.95), 0.10, rnd(-0.55, 0.55));
      p.rotation.y = Math.random() < 0.5 ? 0 : Math.PI / 2;
      nodeGrp.add(p);
    }
    const nlbl = makeLabel('yeraltı düğümü · 18 cm', { scale: 0.34, size: 42 });
    nlbl.position.set(0, 1.3, 0); nlbl.scale.set(nlbl.userData.aspect * 0.34, 0.34, 1);
    nodeGrp.add(nlbl);

    /* --- biyomimetik elektrotlar --- */
    const steelM = new T.MeshPhysicalMaterial({ color: 0xb6bcc2, roughness: 0.3, metalness: 1, clearcoat: 0.2 });
    const graphiteM = new T.MeshStandardMaterial({ color: 0x2b2e31, roughness: 0.62, metalness: 0.35 });
    const gelM = new T.MeshPhysicalMaterial({ color: 0xc6ead9, roughness: 0.16, metalness: 0,
      transmission: 0.8, thickness: 0.5, ior: 1.36, transparent: true, opacity: 0.75,
      clearcoat: 0.85, clearcoatRoughness: 0.12,
      attenuationColor: new T.Color(0x6ac9a4), attenuationDistance: 1.2 });
    const wireM = new T.MeshStandardMaterial({ color: 0xd8bd45, roughness: 0.42, metalness: 0.55 });
    [[-2.9, -1.3], [-1.7, 1.5], [2.5, -1.4], [3.4, 1.4]].forEach((p) => {
      const g = new T.Group(); g.position.set(p[0], 0, p[1]);
      const rod = new T.Mesh(new T.CylinderGeometry(0.052, 0.052, 1.5, 14), steelM);
      rod.position.y = -0.55; rod.castShadow = true; g.add(rod);
      const graph = new T.Mesh(new T.CylinderGeometry(0.1, 0.115, 0.75, 16), graphiteM);
      graph.position.y = -1.02; graph.castShadow = true; g.add(graph);
      const gel = new T.Mesh(new T.CapsuleGeometry(0.155, 0.62, 6, 18), gelM);
      gel.position.y = -1.06; g.add(gel);
      const tip = new T.Mesh(new T.SphereGeometry(0.13, 16, 12),
        new T.MeshBasicMaterial({ color: 0x2fa87c, transparent: true, opacity: 0.7 }));
      tip.position.y = -1.52; g.add(tip);
      const cv = new T.CatmullRomCurve3([
        new T.Vector3(0, -0.02, 0),
        new T.Vector3(-p[0] * 0.35, 0.42, -p[1] * 0.35),
        new T.Vector3(-p[0], 0.06, -p[1])]);
      const wire = new T.Mesh(new T.TubeGeometry(cv, 22, 0.032, 7, false), wireM);
      wire.castShadow = true; g.add(wire);
      rod.userData.hotspot = graph.userData.hotspot = gel.userData.hotspot = 'electrode';
      S.hot.push(rod, graph, gel);
      nodeGrp.add(g);
      electrodeTips.push({ tip });
    });

    /* --- RS485 kablosu --- */
    const cbt = TX.cable();
    const cc = new T.CatmullRomCurve3([
      new T.Vector3(0.4, -1.25, 2.3), new T.Vector3(2.2, -1.08, 3.1),
      new T.Vector3(4.1, -0.58, 3.6), new T.Vector3(5.2, 0.35, 3.6), new T.Vector3(5.2, 1.85, 3.6)]);
    const cable = new T.Mesh(new T.TubeGeometry(cc, 80, 0.082, 10, false),
      new T.MeshStandardMaterial({ map: cbt.map, normalMap: cbt.normalMap,
        normalScale: new T.Vector2(0.8, 0.8), roughness: 0.72, metalness: 0.08 }));
    cable.castShadow = true; micro.add(cable);
    for (let i = 0; i < 4; i++) {
      const s = new T.Mesh(new T.SphereGeometry(0.085, 10, 8), new T.MeshBasicMaterial({ color: 0xc8781a }));
      micro.add(s); cableFlow.push({ mesh: s, curve: cc, u: i / 4 });
    }

    /* --- yüzey düğümü --- */
    surfGrp = new T.Group(); surfGrp.position.set(5.2, 1.95, 3.6); micro.add(surfGrp);
    const mast = new T.Mesh(new T.CylinderGeometry(0.10, 0.13, 2.2, 12),
      new T.MeshStandardMaterial({ color: 0x8b8578, roughness: 0.82, metalness: 0.12 }));
    mast.position.set(5.2, 0.55, 3.6); mast.castShadow = true; micro.add(mast);
    const enc = new T.Mesh(roundedBox(1.6, 1.1, 1.0, 0.09, 4), new T.MeshPhysicalMaterial({
      color: 0x3c4a42, roughness: 0.44, metalness: 0.15, clearcoat: 0.4, clearcoatRoughness: 0.3 }));
    enc.castShadow = true; enc.userData.hotspot = 'surface'; surfGrp.add(enc); S.hot.push(enc);
    const st = TX.solar();
    const panel = new T.Mesh(new T.BoxGeometry(2.8, 0.07, 1.8), new T.MeshPhysicalMaterial({
      map: st.map, roughness: 0.12, metalness: 0.25, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.4 }));
    panel.position.set(0, 1.0, 0); panel.rotation.x = -0.36; panel.castShadow = true;
    panel.userData.hotspot = 'panel'; surfGrp.add(panel); S.hot.push(panel);
    const frame = new T.Mesh(new T.BoxGeometry(2.92, 0.05, 1.92),
      new T.MeshStandardMaterial({ color: 0xa8adb2, roughness: 0.34, metalness: 0.9 }));
    frame.position.set(0, 0.955, 0); frame.rotation.x = -0.36; surfGrp.add(frame);
    const ant = new T.Mesh(new T.CylinderGeometry(0.042, 0.05, 2.3, 12), new T.MeshPhysicalMaterial({
      color: 0x22262a, roughness: 0.35, metalness: 0.3, clearcoat: 0.6 }));
    ant.position.set(0.9, 1.35, 0); ant.castShadow = true;
    ant.userData.hotspot = 'lora'; surfGrp.add(ant); S.hot.push(ant);
    const slbl = makeLabel('yüzey düğümü · güneş + LoRa', { scale: 0.3, size: 40 });
    slbl.position.set(0, 2.75, 0); slbl.scale.set(slbl.userData.aspect * 0.3, 0.3, 1);
    surfGrp.add(slbl);

    const waves = new T.Group(); waves.position.set(0.9, 2.55, 0);
    for (let i = 0; i < 3; i++) {
      const r = new T.Mesh(new T.TorusGeometry(0.5 + i * 0.5, 0.025, 6, 32),
        new T.MeshBasicMaterial({ color: 0x1a7f5a, transparent: true, opacity: 0.4 }));
      r.rotation.x = Math.PI / 2; waves.add(r);
    }
    surfGrp.add(waves); surfGrp.userData.waves = waves;
  }

  /* ========================================================= SAHA DÜNYASI = */
  const SITES = [{ x: -46, z: 18 }, { x: 34, z: 44 }, { x: 58, z: -32 }, { x: -28, z: -52 }];
  let loraLines = [], packets = [], fireGroup, emberPts, smokePts, siteGroups = [];

  function buildMacro() {
    macro = new T.Group(); macro.visible = false; scene.add(macro);

    const g = new T.PlaneGeometry(340, 340, 128, 128);
    g.rotateX(-Math.PI / 2);
    const pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++) pos.setY(i, terrainH(pos.getX(i), pos.getZ(i)));
    g.computeVertexNormals();
    const tt = TX.terrain();
    const ground = new T.Mesh(g, new T.MeshStandardMaterial({
      map: tt.map, normalMap: tt.normalMap, normalScale: new T.Vector2(1.4, 1.4),
      roughness: 0.98, metalness: 0 }));
    ground.receiveShadow = true; macro.add(ground);

    /* Dört katlı iğne yapraklı gövde — tek geometride birleştirilmiş, aşağı
       doğru sarkan etekler ve hafif düzensizlikle oyuncak koni etkisi kırılır */
    const N = 420;
    const trunkG = new T.CylinderGeometry(0.20, 0.52, 6.4, 8); trunkG.translate(0, 3.2, 0);
    function tier(r, h, y, seg) {
      const g = new T.ConeGeometry(r, h, seg || 9, 2);
      const p = g.attributes.position;
      for (let i = 0; i < p.count; i++) {                 // etekleri aşağı sarkıt
        const py = p.getY(i), t = 1 - (py + h / 2) / h;
        const k = 1 + t * t * 0.22;
        p.setX(i, p.getX(i) * k * (0.9 + Math.random() * 0.22));
        p.setZ(i, p.getZ(i) * k * (0.9 + Math.random() * 0.22));
        p.setY(i, py - t * t * h * 0.10);
      }
      g.translate(0, y, 0); g.computeVertexNormals();
      return g;
    }
    const canG  = tier(1.55, 5.2, 11.4);
    const canG2 = tier(2.30, 5.4, 8.6);
    const canG3 = tier(3.05, 5.6, 5.8);
    const canG4 = tier(3.70, 4.6, 3.6);
    const trunk = new T.InstancedMesh(trunkG,
      new T.MeshStandardMaterial({ color: 0x5c4630, roughness: 0.99, metalness: 0, flatShading: true }), N);
    const leafA = new T.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95, metalness: 0, flatShading: true });
    const can1 = new T.InstancedMesh(canG,  leafA, N);
    const can2 = new T.InstancedMesh(canG2, leafA.clone(), N);
    const can3 = new T.InstancedMesh(canG3, leafA.clone(), N);
    const can4 = new T.InstancedMesh(canG4, leafA.clone(), N);
    [trunk, can1, can2, can3, can4].forEach(o => { o.castShadow = true; o.receiveShadow = true; });
    const m = new T.Matrix4(), q = new T.Quaternion(), sv = new T.Vector3(), pv = new T.Vector3();
    const cA = new T.Color(0x1e3a1c), cB = new T.Color(0x476b30);
    const e = new T.Euler();
    let k = 0;
    for (let i = 0; i < N * 5 && k < N; i++) {
      const x = rnd(-152, 152), z = rnd(-152, 152);
      if (Math.hypot(x, z) < 17) continue;
      if (SITES.some(s => Math.hypot(x - s.x, z - s.z) < 10)) continue;
      const s = rnd(0.55, 1.6);
      pv.set(x, terrainH(x, z) - 0.4, z);
      sv.set(s * rnd(0.84, 1.18), s * rnd(0.9, 1.25), s * rnd(0.84, 1.18));
      e.set(rnd(-0.06, 0.06), rnd(0, 6.28), rnd(-0.06, 0.06));
      q.setFromEuler(e);
      m.compose(pv, q, sv);
      trunk.setMatrixAt(k, m);
      [can1, can2, can3, can4].forEach(c => c.setMatrixAt(k, m));
      const col = cA.clone().lerp(cB, Math.pow(Math.random(), 0.8));
      can1.setColorAt(k, col.clone().multiplyScalar(1.22));   // tepe daha aydınlık
      can2.setColorAt(k, col.clone().multiplyScalar(1.05));
      can3.setColorAt(k, col.clone().multiplyScalar(0.88));
      can4.setColorAt(k, col.clone().multiplyScalar(0.72));   // etek gölgede
      k++;
    }
    trunk.count = can1.count = can2.count = can3.count = can4.count = k;
    [trunk, can1, can2, can3, can4].forEach(o => {
      o.instanceMatrix.needsUpdate = true;
      if (o.instanceColor) o.instanceColor.needsUpdate = true;
    });
    macro.add(trunk, can1, can2, can3, can4);

    /* kule */
    const tower = new T.Group();
    const ty = terrainH(0, 0); tower.position.set(0, ty, 0);
    const galv = new T.MeshPhysicalMaterial({ color: 0x9aa1a7, roughness: 0.42, metalness: 0.95, clearcoat: 0.2 });
    for (let i = 0; i < 4; i++) {
      const a = i * Math.PI / 2 + Math.PI / 4;
      const leg = new T.Mesh(new T.CylinderGeometry(0.11, 0.17, 20, 8), galv);
      leg.position.set(Math.cos(a) * 1.5, 10, Math.sin(a) * 1.5);
      leg.rotation.z = -Math.cos(a) * 0.075; leg.rotation.x = Math.sin(a) * 0.075;
      leg.castShadow = true; tower.add(leg);
    }
    for (let h = 2.6; h < 20; h += 2.6) {
      const ring = new T.Mesh(new T.TorusGeometry(1.45 * (1 - h / 48), 0.05, 6, 4), galv);
      ring.rotation.x = Math.PI / 2; ring.position.y = h; tower.add(ring);
    }
    const box = new T.Mesh(roundedBox(1.6, 2.1, 1.2, 0.1, 3), new T.MeshPhysicalMaterial({
      color: 0x39443d, roughness: 0.42, metalness: 0.3, clearcoat: 0.4 }));
    box.position.set(1.7, 6.6, 0); box.castShadow = true;
    box.userData.hotspot = 'rak2287'; tower.add(box); S.hot.push(box);
    const dish = new T.Mesh(new T.SphereGeometry(1.3, 24, 14, 0, 6.283, 0, 1.0),
      new T.MeshPhysicalMaterial({ color: 0xeceff1, roughness: 0.3, metalness: 0.15,
        side: T.DoubleSide, clearcoat: 0.5 }));
    dish.position.set(0, 19.4, 0); dish.rotation.x = 2.4; dish.castShadow = true; tower.add(dish);
    const beacon = new T.Mesh(new T.SphereGeometry(0.3, 14, 12), new T.MeshBasicMaterial({ color: 0xd8352a }));
    beacon.position.y = 21; tower.add(beacon); tower.userData.beacon = beacon;
    const tl = makeLabel('Aegis-Nexus · RAK2287 + RPi 4', { scale: 2.0, size: 44 });
    tl.position.set(0, 25.5, 0); tl.scale.set(tl.userData.aspect * 2.0, 2.0, 1);
    tower.add(tl);
    macro.add(tower); macro.userData.tower = tower;

    const st = TX.solar();
    SITES.forEach((s, i) => {
      const grp = new T.Group(); const y = terrainH(s.x, s.z);
      grp.position.set(s.x, y, s.z);
      const post = new T.Mesh(new T.CylinderGeometry(0.1, 0.12, 2.8, 8),
        new T.MeshStandardMaterial({ color: 0x7d7566, roughness: 0.86, metalness: 0.1 }));
      post.position.y = 1.4; post.castShadow = true; grp.add(post);
      const panel = new T.Mesh(new T.BoxGeometry(1.6, 0.07, 1.05), new T.MeshPhysicalMaterial({
        map: st.map, roughness: 0.12, metalness: 0.25, clearcoat: 1, clearcoatRoughness: 0.05 }));
      panel.position.set(0, 2.8, 0); panel.rotation.x = -0.42; panel.castShadow = true;
      panel.userData.hotspot = 'panel'; grp.add(panel); S.hot.push(panel);
      const enc = new T.Mesh(roundedBox(0.5, 0.68, 0.38, 0.05, 3), new T.MeshPhysicalMaterial({
        color: 0x3a463e, roughness: 0.45, metalness: 0.2, clearcoat: 0.4 }));
      enc.position.set(0, 1.95, 0.24); enc.castShadow = true;
      enc.userData.hotspot = 'node'; grp.add(enc); S.hot.push(enc);
      const ant = new T.Mesh(new T.CylinderGeometry(0.03, 0.035, 1.6, 8),
        new T.MeshStandardMaterial({ color: 0x2a2e32, roughness: 0.4, metalness: 0.35 }));
      ant.position.set(0.36, 3.3, 0); grp.add(ant);
      const beam = new T.Mesh(new T.CylinderGeometry(0.3, 0.3, 1.9, 12, 1, true),
        new T.MeshBasicMaterial({ color: 0x1a7f5a, transparent: true, opacity: 0.16,
          side: T.DoubleSide, depthWrite: false }));
      beam.position.y = -0.95; grp.add(beam);
      const tip = new T.Mesh(new T.SphereGeometry(0.17, 14, 12), new T.MeshBasicMaterial({ color: 0x1a7f5a }));
      tip.position.y = -1.85; grp.add(tip);
      grp.add(new T.Line(new T.BufferGeometry().setFromPoints(
        [new T.Vector3(0, 3.6, 0), new T.Vector3(0, 16.4, 0)]),
        new T.LineBasicMaterial({ color: 0x1a7f5a, transparent: true, opacity: 0.3 })));
      const lbl = makeLabel('düğüm ' + 'ABCD'[i] + ' · 18 cm', { scale: 1.5, size: 42 });
      lbl.position.set(0, 17.4, 0); lbl.scale.set(lbl.userData.aspect * 1.5, 1.5, 1);
      grp.add(lbl);
      grp.userData = { tip, beam };
      macro.add(grp); siteGroups.push(grp);

      const from = new T.Vector3(s.x, y + 3.4, s.z), to = new T.Vector3(0, ty + 19, 0);
      const mid = from.clone().add(to).multiplyScalar(0.5); mid.y += from.distanceTo(to) * 0.22;
      const curve = new T.QuadraticBezierCurve3(from, mid, to);
      const line = new T.Line(new T.BufferGeometry().setFromPoints(curve.getPoints(64)),
        new T.LineBasicMaterial({ color: 0x1a7f5a, transparent: true, opacity: 0.2 }));
      macro.add(line); loraLines.push({ line });
      for (let p = 0; p < 2; p++) {
        const sp = new T.Mesh(new T.SphereGeometry(0.32, 12, 10), new T.MeshBasicMaterial({ color: 0x0f6b4a }));
        macro.add(sp); packets.push({ mesh: sp, curve, u: Math.random(), speed: rnd(0.16, 0.26) });
      }
    });

    /* yangın */
    fireGroup = new T.Group(); fireGroup.visible = false; macro.add(fireGroup);
    const fx = 66, fz = 60, fy = terrainH(fx, fz);
    fireGroup.position.set(fx, fy, fz);
    const glow = new T.Mesh(new T.CircleGeometry(13, 40),
      new T.MeshBasicMaterial({ color: 0xff6a2a, transparent: true, opacity: 0.5, depthWrite: false }));
    glow.rotation.x = -Math.PI / 2; glow.position.y = 0.35; fireGroup.add(glow);
    fireGroup.userData.glow = glow;

    const eN = 520, ep = new Float32Array(eN * 3), ev = [];
    for (let i = 0; i < eN; i++) {
      const a = rnd(0, 6.283), r = Math.sqrt(Math.random()) * 12;
      ep[i * 3] = Math.cos(a) * r; ep[i * 3 + 1] = rnd(0, 3); ep[i * 3 + 2] = Math.sin(a) * r;
      ev.push({ vy: rnd(2.5, 8), a, r });
    }
    const eg = new T.BufferGeometry(); eg.setAttribute('position', new T.BufferAttribute(ep, 3));
    emberPts = new T.Points(eg, new T.PointsMaterial({ size: 1.4, map: dotTex, color: 0xffa040,
      transparent: true, opacity: 0.9, blending: T.AdditiveBlending, depthWrite: false }));
    emberPts.userData.v = ev; fireGroup.add(emberPts);

    const sN = 320, sp2 = new Float32Array(sN * 3), sv2 = [];
    for (let i = 0; i < sN; i++) {
      const a = rnd(0, 6.283), r = Math.sqrt(Math.random()) * 14;
      sp2[i * 3] = Math.cos(a) * r; sp2[i * 3 + 1] = rnd(2, 40); sp2[i * 3 + 2] = Math.sin(a) * r;
      sv2.push({ vy: rnd(3, 7), a, r });
    }
    const sg = new T.BufferGeometry(); sg.setAttribute('position', new T.BufferAttribute(sp2, 3));
    smokePts = new T.Points(sg, new T.PointsMaterial({ size: 17, map: dotTex, color: 0x8b8378,
      transparent: true, opacity: 0.2, depthWrite: false }));
    smokePts.userData.v = sv2; fireGroup.add(smokePts);

    fireLight = new T.PointLight(0xff7a35, 0, 100, 2);
    fireLight.position.set(fx, fy + 6, fz); macro.add(fireLight);
  }

  /* ================================================================ INIT == */
  function init(canvas) {
    dotTex = TX.dot();
    renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = T.PCFSoftShadowMap;

    scene = new T.Scene();
    scene.background = new T.Color(0xeef1f4);
    camera = new T.PerspectiveCamera(38, 1, 0.05, 2000);

    pmrem = new T.PMREMGenerator(renderer);
    pmrem.compileEquirectangularShader();
    const skyTex = TX.skyEquirect(0.62, 0.9, 1.0);
    envRT = pmrem.fromEquirectangular(skyTex);
    scene.environment = envRT.texture;
    skyTex.dispose();

    hemi = new T.HemisphereLight(0xcfe2f2, 0x6f6a52, 1.1); scene.add(hemi);
    sun = new T.DirectionalLight(0xfff4e2, 2.5);
    sun.position.set(26, 34, 22);
    sun.castShadow = true;
    sun.shadow.mapSize.set(1536, 1536);
    sun.shadow.camera.near = 1; sun.shadow.camera.far = 120;
    sun.shadow.camera.left = -26; sun.shadow.camera.right = 26;
    sun.shadow.camera.top = 26; sun.shadow.camera.bottom = -26;
    sun.shadow.bias = -0.0008; sun.shadow.normalBias = 0.03;
    scene.add(sun); scene.add(sun.target);
    fill = new T.DirectionalLight(0xdcecff, 0.55); fill.position.set(-24, 14, -18); scene.add(fill);

    buildMicro();
    buildMacro();
    setView('sub', true);
    resize();
    S.ready = true;
    return { renderer, scene, camera };
  }

  /* ============================================================== KAMERA == */
  function setView(name, instant) {
    const v = VIEWS[name] || VIEWS.sub;
    S.view = name;
    if (v.mode !== S.mode) setMode(v.mode);
    cam.posT.set(v.pos[0], v.pos[1], v.pos[2]);
    cam.tgtT.set(v.tgt[0], v.tgt[1], v.tgt[2]);
    cam.fovT = v.fov;
    orbit.speed = v.orbit; orbit.sweep = v.sweep;
    orbit.radius = Math.hypot(v.pos[0], v.pos[2]);
    orbit.a = orbit.a0 = Math.atan2(v.pos[0], v.pos[2]);
    orbit.baseY = v.pos[1];
    orbit.userA = 0; orbit.userB = 0;
    const k = v.mode === 'macro' ? 5 : 1;
    sun.shadow.camera.left = -26 * k; sun.shadow.camera.right = 26 * k;
    sun.shadow.camera.top = 26 * k; sun.shadow.camera.bottom = -26 * k;
    sun.shadow.camera.far = 130 * k;
    sun.position.set(26 * k * 0.7, 34 * k * 0.7, 22 * k * 0.7);
    sun.shadow.camera.updateProjectionMatrix();
    if (instant) {
      cam.pos.copy(cam.posT); cam.tgt.copy(cam.tgtT);
      camera.fov = cam.fovT; camera.updateProjectionMatrix();
      camera.position.copy(cam.pos); camera.lookAt(cam.tgt);
    }
  }
  function setMode(m) {
    S.mode = m;
    macro.visible = (m === 'macro'); micro.visible = (m === 'micro');
    /* saha ölçeğinde hava perspektifi; kesitte sis yok */
    scene.fog = (m === 'macro') ? new T.Fog(0xdfe7ee, 150, 400) : null;
    hemi.intensity = (m === 'macro') ? 0.72 : 1.1;
    fill.intensity = (m === 'macro') ? 0.34 : 0.55;
    renderer.toneMappingExposure = (m === 'macro') ? 1.08 : 1.0;
  }

  function bindInput(el, onPick) {
    let moved = 0;
    el.addEventListener('pointerdown', (e) => {
      orbit.drag = true; orbit.px = e.clientX; orbit.py = e.clientY; moved = 0;
      try { el.setPointerCapture(e.pointerId); } catch (_) {}
    });
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      S.mouse = { x: (e.clientX - r.left) / r.width * 2 - 1, y: -((e.clientY - r.top) / r.height * 2 - 1) };
      if (!orbit.drag) return;
      const dx = e.clientX - orbit.px, dy = e.clientY - orbit.py;
      orbit.userA -= dx * 0.005; orbit.userB = clamp(orbit.userB - dy * 0.004, -0.5, 0.95);
      orbit.px = e.clientX; orbit.py = e.clientY; moved += Math.abs(dx) + Math.abs(dy);
    });
    el.addEventListener('pointerup', () => {
      orbit.drag = false;
      if (moved < 6 && onPick) { const id = pick(); if (id) onPick(id); }
    });
    el.addEventListener('pointercancel', () => { orbit.drag = false; });
    el.addEventListener('wheel', (e) => {
      e.preventDefault();
      const lo = S.mode === 'macro' ? 34 : 9, hi = S.mode === 'macro' ? 260 : 60;
      orbit.radius = clamp(orbit.radius * (1 + Math.sign(e.deltaY) * 0.08), lo, hi);
    }, { passive: false });
  }

  const ray = new T.Raycaster();
  function pick() {
    if (!S.mouse) return null;
    ray.setFromCamera(new T.Vector2(S.mouse.x, S.mouse.y), camera);
    const list = S.hot.filter(o => { let p = o; while (p) { if (p === macro || p === micro) return p.visible; p = p.parent; } return false; });
    const hits = ray.intersectObjects(list, true);
    for (const h of hits) { let o = h.object; while (o) { if (o.userData && o.userData.hotspot) return o.userData.hotspot; o = o.parent; } }
    return null;
  }

  /* ============================================================ GÜNCELLE == */
  const tmp = new T.Vector3();
  let clockT = 0;

  function update(dt, ctx) {
    if (!S.ready) return;
    clockT += dt;
    const fire = ctx.fireIntensity || 0;

    if (!orbit.drag && ctx.autoOrbit !== false && !orbit.sweep) orbit.a += orbit.speed * dt;
    const A = (orbit.sweep ? orbit.a0 + orbit.sweep * Math.sin(clockT * orbit.speed) : orbit.a) + orbit.userA;
    cam.posT.x = Math.sin(A) * orbit.radius;
    cam.posT.z = Math.cos(A) * orbit.radius;
    cam.posT.y = orbit.baseY + orbit.userB * orbit.radius * 0.5;
    const k = 1 - Math.exp(-dt * 3.2);
    cam.pos.lerp(cam.posT, k); cam.tgt.lerp(cam.tgtT, k);
    camera.fov += (cam.fovT - camera.fov) * k; camera.updateProjectionMatrix();
    camera.position.copy(cam.pos); camera.lookAt(cam.tgt);
    sun.target.position.copy(cam.tgt); sun.target.updateMatrixWorld();

    scene.background.setRGB(0.933 - fire * 0.20, 0.945 - fire * 0.34, 0.957 - fire * 0.44);
    sun.intensity = 2.5 - fire * 1.1;
    hemi.intensity = (S.mode === 'macro' ? 0.72 : 1.1) - fire * 0.3;
    hemi.color.setRGB(0.81 + fire * 0.18, 0.886 - fire * 0.22, 0.949 - fire * 0.4);

    if (S.mode === 'micro') updateMicro(dt, ctx); else updateMacro(dt, ctx);
    renderer.render(scene, camera);
  }

  function updateMicro(dt, ctx) {
    const w = ctx.world;
    layerMeshes.forEach((m) => {
      const L = m.userData.layer, zc = (L.z0 + L.z1) / 2;
      const Tz = w ? w.Tz(zc) : 22, amb = w ? w.p.tAmb : 22;
      const u = clamp((Tz - amb) / 55, 0, 1);
      const hc = AEGIS_CHART.heatColor(Tz);
      m.material.color.setRGB(
        1 + u * (hc[0] / 255 * 1.9 - 1),
        1 + u * (hc[1] / 255 * 1.5 - 1),
        1 + u * (hc[2] / 255 * 1.1 - 1));
      const e = clamp((Tz - 90) / 400, 0, 1);
      m.material.emissive.setRGB(e * 0.95, e * 0.26, e * 0.04);
      m.material.emissiveIntensity = e * 2.0;
      const th = w ? w.thetaZ(zc) : 0.22;
      m.material.roughness = clamp(1.04 - th * 0.5, 0.62, 1.0);
    });

    safeBand.material.opacity = 0.07 + 0.05 * (0.5 + 0.5 * Math.sin(clockT * 1.8));
    if (ctx.alarm) {
      safeBand.material.color.setHex(0xc0392b);
      safeBand.material.opacity = 0.1 + 0.12 * (0.5 + 0.5 * Math.sin(clockT * 9));
    } else safeBand.material.color.setHex(0x1a7f5a);

    if (hyphaGeo) {
      hyphaGeo.setDrawRange(0, Math.floor(hyphaGeo.attributes.position.count * clamp(S.growth, 0, 1)));
      hyphaLine.material.opacity = 0.6 + 0.3 * (w ? (w.stress || 0) : 0);
    }

    const f = w && w.cond ? w.cond.f : 0.4;
    const active = clamp(Math.round(6 + f * 24), 4, pulses.length);
    const pa = pulsePts.geometry.attributes.position;
    for (let i = 0; i < pulses.length; i++) {
      const p = pulses[i];
      if (i < active) {
        p.u += p.speed * dt * (0.6 + f * 0.9);
        if (p.u > 1) { p.u = 0; p.path = hyphaPaths[(Math.random() * hyphaPaths.length) | 0]; }
        if (p.path) { p.path.getPointAt(clamp(p.u, 0, 1), tmp); pa.setXYZ(i, tmp.x, tmp.y, tmp.z); }
      } else pa.setXYZ(i, 0, 999, 0);
    }
    pa.needsUpdate = true;
    pulsePts.material.color.setHex(ctx.alarm ? 0xc0392b : 0x0f6b4a);
    pulsePts.material.size = 0.32 + 0.26 * clamp(f / 3, 0, 1);

    electrodeTips.forEach((e, i) => {
      const p = 0.5 + 0.5 * Math.sin(clockT * (2 + i * 0.7) + i);
      e.tip.material.opacity = 0.3 + 0.5 * p * (0.4 + (w ? w.stress || 0 : 0));
      e.tip.scale.setScalar(0.85 + 0.3 * p);
    });

    cableFlow.forEach((c) => {
      c.u += dt * 0.28; if (c.u > 1) c.u -= 1;
      c.curve.getPointAt(c.u, tmp); c.mesh.position.copy(tmp);
      c.mesh.material.color.setHex(ctx.alarm ? 0xc0392b : 0xc8781a);
    });

    if (surfGrp.userData.waves) surfGrp.userData.waves.children.forEach((r, i) => {
      const ph = (clockT * 0.7 + i * 0.33) % 1;
      r.scale.setScalar(0.4 + ph * 1.8);
      r.material.opacity = (1 - ph) * (ctx.alarm ? 0.7 : 0.3);
      r.material.color.setHex(ctx.alarm ? 0xc0392b : 0x1a7f5a);
    });
  }

  function updateMacro(dt, ctx) {
    const fire = ctx.fireIntensity || 0;
    fireGroup.visible = fire > 0.01;
    fireLight.intensity = fire * (30 + Math.sin(clockT * 13) * 8 + Math.sin(clockT * 4.3) * 5);
    if (fireGroup.visible) {
      const g = fireGroup.userData.glow;
      g.material.opacity = 0.26 + 0.3 * fire * (0.7 + 0.3 * Math.sin(clockT * 7));
      g.scale.setScalar(0.55 + fire * 0.85);
      const ep = emberPts.geometry.attributes.position, ev = emberPts.userData.v;
      for (let i = 0; i < ev.length; i++) {
        let y = ep.getY(i) + ev[i].vy * dt * (0.4 + fire);
        if (y > 34) { y = rnd(0, 2); ev[i].a = rnd(0, 6.283); ev[i].r = Math.sqrt(Math.random()) * 12; }
        ep.setY(i, y);
        ep.setX(i, Math.cos(ev[i].a + y * 0.05) * ev[i].r * (1 + y * 0.02));
        ep.setZ(i, Math.sin(ev[i].a + y * 0.05) * ev[i].r * (1 + y * 0.02));
      }
      ep.needsUpdate = true;
      const sp = smokePts.geometry.attributes.position, sv = smokePts.userData.v;
      for (let i = 0; i < sv.length; i++) {
        let y = sp.getY(i) + sv[i].vy * dt; if (y > 95) y = rnd(2, 8);
        sp.setY(i, y);
        sp.setX(i, Math.cos(sv[i].a + y * 0.02) * (sv[i].r + y * 0.35));
        sp.setZ(i, Math.sin(sv[i].a + y * 0.02) * (sv[i].r + y * 0.35));
      }
      sp.needsUpdate = true;
      smokePts.material.opacity = 0.07 + 0.22 * fire;
    }
    packets.forEach((p) => {
      p.u += p.speed * dt * (ctx.alarm ? 2.4 : 1);
      if (p.u > 1) { p.u = 0; p.mesh.visible = Math.random() < (ctx.alarm ? 1 : 0.22); }
      p.curve.getPointAt(clamp(p.u, 0, 1), tmp);
      p.mesh.position.copy(tmp);
      p.mesh.material.color.setHex(ctx.alarm ? 0xc0392b : 0x0f6b4a);
      p.mesh.scale.setScalar(ctx.alarm ? 1.5 : 1);
    });
    loraLines.forEach(l => { l.line.material.opacity = ctx.alarm ? 0.42 : 0.18; });
    siteGroups.forEach((g, i) => {
      const b = 0.5 + 0.5 * Math.sin(clockT * (ctx.alarm ? 8 : 1.6) + i);
      g.userData.tip.material.color.setHex(ctx.alarm ? 0xc0392b : 0x1a7f5a);
      g.userData.tip.scale.setScalar(0.8 + b * 0.6);
      g.userData.beam.material.color.setHex(ctx.alarm ? 0xc0392b : 0x1a7f5a);
      g.userData.beam.material.opacity = 0.1 + b * 0.14;
    });
    const tw = macro.userData.tower;
    if (tw && tw.userData.beacon) {
      tw.userData.beacon.material.color.setHex(ctx.alarm ? 0xff2a18 : 0xd8352a);
      tw.userData.beacon.scale.setScalar(0.7 + 0.6 * (0.5 + 0.5 * Math.sin(clockT * (ctx.alarm ? 10 : 2.2))));
    }
  }

  function resize() {
    if (!renderer) return;
    const c = renderer.domElement;
    const w = c.clientWidth || 1, h = c.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }

  global.AEGIS_SCENE = {
    init, update, resize, setView, setMode, bindInput, pick, S, VIEWS,
    setGrowth: (g) => { S.growth = g; },
    get mode() { return S.mode; }
  };
})(window);
