// Tipos mínimos do gazetteer GeoNames empacotado em `all-the-cities` (sem tipos próprios).
declare module "all-the-cities" {
  interface Cidade {
    cityId: number;
    name: string;
    altName: string;
    country: string;
    featureCode: string;
    adminCode: string;
    population: number;
    loc: { type: "Point"; coordinates: [number, number] };
  }
  const cidades: Cidade[];
  export default cidades;
}
