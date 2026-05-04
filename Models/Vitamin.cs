namespace VitaminApp.Models
{
    public class Vitamin
    {
        public int Id { get; set; }
        public string Name { get; set; }

        public List<ProductVitamin> ProductVitamins { get; set; }
    }
}