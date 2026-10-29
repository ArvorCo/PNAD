/* Distâncias no elipsoide WGS84, com fallback de grande círculo. */
window.GeoPolitize = (function () {
  function distanciaKm(lat1, lon1, lat2, lon2) {
    const a = 6378137, f = 1 / 298.257223563, b = a * (1 - f);
    const rad = Math.PI / 180;
    const L = (lon2 - lon1) * rad;
    const U1 = Math.atan((1 - f) * Math.tan(lat1 * rad));
    const U2 = Math.atan((1 - f) * Math.tan(lat2 * rad));
    const sinU1 = Math.sin(U1), cosU1 = Math.cos(U1), sinU2 = Math.sin(U2), cosU2 = Math.cos(U2);
    let lambda = L, it = 0, sinS, cosS, sigma, sinAlpha, cos2Alpha, cos2SigmaM, lambdaP;
    do {
      const sinL = Math.sin(lambda), cosL = Math.cos(lambda);
      sinS = Math.sqrt(Math.pow(cosU2 * sinL, 2) + Math.pow(cosU1 * sinU2 - sinU1 * cosU2 * cosL, 2));
      if (sinS === 0) return 0;
      cosS = sinU1 * sinU2 + cosU1 * cosU2 * cosL;
      sigma = Math.atan2(sinS, cosS);
      sinAlpha = cosU1 * cosU2 * sinL / sinS;
      cos2Alpha = 1 - sinAlpha * sinAlpha;
      cos2SigmaM = cos2Alpha !== 0 ? cosS - 2 * sinU1 * sinU2 / cos2Alpha : 0;
      const C = f / 16 * cos2Alpha * (4 + f * (4 - 3 * cos2Alpha));
      lambdaP = lambda;
      lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinS * (cos2SigmaM + C * cosS * (-1 + 2 * cos2SigmaM * cos2SigmaM)));
    } while (Math.abs(lambda - lambdaP) > 1e-12 && ++it < 200);
    if (it >= 200) return haversineKm(lat1, lon1, lat2, lon2);
    const u2 = cos2Alpha * (a * a - b * b) / (b * b);
    const A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)));
    const B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)));
    const dS = B * sinS * (cos2SigmaM + B / 4 * (cosS * (-1 + 2 * cos2SigmaM * cos2SigmaM) - B / 6 * cos2SigmaM * (-3 + 4 * sinS * sinS) * (-3 + 4 * cos2SigmaM * cos2SigmaM)));
    return b * A * (sigma - dS) / 1000;
  }
  function haversineKm(lat1, lon1, lat2, lon2) {
    const rad = Math.PI / 180, dp = (lat2 - lat1) * rad, dl = (lon2 - lon1) * rad;
    const x = Math.pow(Math.sin(dp / 2), 2) + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.pow(Math.sin(dl / 2), 2);
    return 2 * 6371.0088 * Math.asin(Math.min(1, Math.sqrt(x)));
  }
  const coordOk = (l) => typeof l.lat === 'number' && typeof l.lon === 'number' && isFinite(l.lat) && isFinite(l.lon);


return {distanciaKm,haversineKm,coordOk};
})();
