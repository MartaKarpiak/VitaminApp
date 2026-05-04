namespace VitaminApp.Models
{
    public class Dish
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Recipe { get; set; }

        public List<DishProduct> DishProducts { get; set; }
    }
}