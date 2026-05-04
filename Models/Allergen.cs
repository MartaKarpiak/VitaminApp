namespace VitaminApp.Models
{
    public class Allergen
    {
        public int Id { get; set; }
        public string Name { get; set; }

        public List<ProductAllergen> ProductAllergens { get; set; }
    }
}