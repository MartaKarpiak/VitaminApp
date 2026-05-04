namespace VitaminApp.Models
{
    public class Product
    {
        public int Id { get; set; }
        public string Name { get; set; }

        public List<ProductVitamin> ProductVitamins { get; set; }
        public List<ProductAllergen> ProductAllergens { get; set; }
        public List<DishProduct> DishProducts { get; set; }
    }
}