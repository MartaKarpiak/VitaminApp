namespace VitaminApp.Models
{
    public class ProductVitamin
    {
        public int ProductId { get; set; }
        public Product Product { get; set; }

        public int VitaminId { get; set; }
        public Vitamin Vitamin { get; set; }
    }
}