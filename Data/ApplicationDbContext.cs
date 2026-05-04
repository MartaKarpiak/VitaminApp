using Microsoft.EntityFrameworkCore;
using VitaminApp.Models;

namespace VitaminApp.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options) { }

        public DbSet<Product> Products { get; set; }
        public DbSet<Vitamin> Vitamins { get; set; }
        public DbSet<Dish> Dishes { get; set; }
        public DbSet<Allergen> Allergens { get; set; }

        public DbSet<ProductVitamin> ProductVitamins { get; set; }
        public DbSet<ProductAllergen> ProductAllergens { get; set; }
        public DbSet<DishProduct> DishProducts { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<ProductVitamin>()
                .HasKey(pv => new { pv.ProductId, pv.VitaminId });

            modelBuilder.Entity<ProductAllergen>()
                .HasKey(pa => new { pa.ProductId, pa.AllergenId });

            modelBuilder.Entity<DishProduct>()
                .HasKey(dp => new { dp.DishId, dp.ProductId });
        }
    }
}