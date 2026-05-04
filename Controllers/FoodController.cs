using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using VitaminApp.Data;
using VitaminApp.Models;

namespace VitaminApp.Controllers
{
    public class FoodController : Controller
    {
        private readonly ApplicationDbContext _context;

        public FoodController(ApplicationDbContext context)
        {
            _context = context;
        }

        public IActionResult Index()
        {
            var vitamins = _context.Vitamins.ToList();
            return View(vitamins);
        }

        [HttpPost]
        public IActionResult Search(string vitaminName, string allergenName)
        {
            var products = _context.Products
                .Include(p => p.ProductVitamins)
                .ThenInclude(pv => pv.Vitamin)
                .Where(p => p.ProductVitamins.Any(pv => pv.Vitamin.Name == vitaminName))
                .ToList();

            if (!string.IsNullOrEmpty(allergenName))
            {
                products = products
                    .Where(p => !p.ProductAllergens
                        .Any(pa => pa.Allergen.Name == allergenName))
                    .ToList();
            }

            var dishes = _context.Dishes
                .Include(d => d.DishProducts)
                .ThenInclude(dp => dp.Product)
                .ThenInclude(p => p.ProductVitamins)
                .ThenInclude(pv => pv.Vitamin)
                .Where(d => d.DishProducts.Any(dp =>
                    dp.Product.ProductVitamins.Any(pv => pv.Vitamin.Name == vitaminName)))
                .ToList();

            ViewBag.Products = products;
            ViewBag.Dishes = dishes;

            return View("Results");
        }
    }
}