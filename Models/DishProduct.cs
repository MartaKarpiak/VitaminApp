namespace VitaminApp.Models
{
    public class DishProduct
    {
        public int DishId { get; set; }
        public Dish Dish { get; set; }

        public int ProductId { get; set; }
        public Product Product { get; set; }
    }
}