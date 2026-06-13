
export interface Opt {
  key: string
  label: string
  note?: string
  emoji?: string
}

export const DIET_TYPES: Opt[] = [
  { key: "vegetarian", label: "Vegetarian", note: "No meat, fish or eggs", emoji: "🥗" },
  { key: "eggetarian", label: "Eggetarian", note: "Vegetarian + eggs", emoji: "🥚" },
  { key: "non-vegetarian", label: "Non-vegetarian", note: "Eats meat & seafood", emoji: "🍗" },
  { key: "vegan", label: "Vegan", note: "No animal products", emoji: "🌱" },
  { key: "pescatarian", label: "Pescatarian", note: "Vegetarian + seafood", emoji: "🐟" },
  { key: "jain", label: "Jain", note: "No onion, garlic or roots", emoji: "🙏" },
  { key: "halal", label: "Halal", note: "Halal-prepared only", emoji: "☪" },
]

export const GENDERS: Opt[] = [
  { key: "female", label: "Female", emoji: "♀" },
  { key: "male", label: "Male", emoji: "♂" },
  { key: "non-binary", label: "Non-binary", emoji: "⚧" },
  { key: "undisclosed", label: "Prefer not to say", emoji: "•" },
]

export const SPICE: Opt[] = [
  { key: "mild", label: "Mild", emoji: "🌤" },
  { key: "medium", label: "Medium", emoji: "🌶" },
  { key: "spicy", label: "Spicy", emoji: "🔥" },
  { key: "fiery", label: "Fiery", emoji: "🌋" },
]

export const ALLERGENS: Opt[] = [
  { key: "peanuts", label: "Peanuts" },
  { key: "tree nuts", label: "Tree nuts" },
  { key: "milk", label: "Milk / Dairy" },
  { key: "eggs", label: "Eggs" },
  { key: "soy", label: "Soy" },
  { key: "wheat", label: "Wheat / Gluten" },
  { key: "fish", label: "Fish" },
  { key: "shellfish", label: "Shellfish" },
  { key: "sesame", label: "Sesame" },
  { key: "mustard", label: "Mustard" },
  { key: "sulphites", label: "Sulphites" },
]

export const GOALS: Opt[] = [
  { key: "high-protein", label: "High protein", emoji: "💪" },
  { key: "heart-healthy", label: "Heart healthy", emoji: "❤️" },
  { key: "weight-loss", label: "Weight loss", emoji: "⚖️" },
  { key: "muscle-gain", label: "Muscle gain", emoji: "🏋️" },
  { key: "low-carb", label: "Low-carb / Keto", emoji: "🥑" },
  { key: "diabetic-friendly", label: "Diabetic-friendly", emoji: "🩸" },
  { key: "gut-health", label: "Gut health", emoji: "🌾" },
  { key: "low-sodium", label: "Low sodium", emoji: "🧂" },
  { key: "balanced", label: "Balanced wellness", emoji: "🧘" },
  { key: "plant-forward", label: "Plant-forward", emoji: "🥬" },
  { key: "immunity", label: "Immunity", emoji: "🛡️" },
]

export const CUISINES: Opt[] = [
  "Bengali", "Mughlai", "North Indian", "South Indian", "Punjabi",
  "Chinese", "Italian", "Continental", "Thai", "Japanese", "Mexican",
  "Cafe", "Street Food",
].map((c) => ({ key: c.toLowerCase(), label: c }))

type FoodKind = "vegan" | "veg" | "egg" | "seafood" | "meat"
export const FOODS: { name: string; kind: FoodKind }[] = [
  { name: "Masala Dosa", kind: "vegan" },
  { name: "Chaat", kind: "vegan" },
  { name: "Idli", kind: "vegan" },
  { name: "Khichuri", kind: "vegan" },
  { name: "Veg Momos", kind: "vegan" },
  { name: "Hummus", kind: "vegan" },
  { name: "Falafel", kind: "vegan" },
  { name: "Cold Brew", kind: "vegan" },
  { name: "Paneer Tikka", kind: "veg" },
  { name: "Margherita Pizza", kind: "veg" },
  { name: "Pasta Alfredo", kind: "veg" },
  { name: "Chole Bhature", kind: "veg" },
  { name: "Veg Thali", kind: "veg" },
  { name: "Filter Coffee", kind: "veg" },
  { name: "Gulab Jamun", kind: "veg" },
  { name: "Ice Cream", kind: "veg" },
  { name: "Egg Curry", kind: "egg" },
  { name: "Masala Omelette", kind: "egg" },
  { name: "Egg Roll", kind: "egg" },
  { name: "Fish Curry", kind: "seafood" },
  { name: "Sushi", kind: "seafood" },
  { name: "Prawn Tempura", kind: "seafood" },
  { name: "Chicken Biryani", kind: "meat" },
  { name: "Butter Chicken", kind: "meat" },
  { name: "Tandoori Chicken", kind: "meat" },
  { name: "Mutton Kebab", kind: "meat" },
  { name: "Ramen", kind: "meat" },
  { name: "Kathi Roll", kind: "meat" },
]

const ALLOWED_KINDS: Record<string, FoodKind[]> = {
  vegan: ["vegan"],
  vegetarian: ["vegan", "veg"],
  jain: ["vegan", "veg"],
  eggetarian: ["vegan", "veg", "egg"],
  pescatarian: ["vegan", "veg", "egg", "seafood"],
  "non-vegetarian": ["vegan", "veg", "egg", "seafood", "meat"],
  halal: ["vegan", "veg", "egg", "seafood", "meat"],
}

export const ALL_FOOD_NAMES = FOODS.map((f) => f.name)

export function foodsForDiet(diet?: string): string[] {
  const kinds = ALLOWED_KINDS[diet || "non-vegetarian"] || ["vegan", "veg", "egg", "seafood", "meat"]
  return FOODS.filter((f) => kinds.includes(f.kind)).map((f) => f.name)
}
