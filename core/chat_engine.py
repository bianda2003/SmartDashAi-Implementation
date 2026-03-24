class ChatEngine:
    """
    Safe, intent-based AI assistant for data exploration.
    NO eval / exec.
    """

    def __init__(self, df):
        self.df = df

    def generate_response(self, user_input: str) -> str:
        """
        Interprets user questions and maps them
        to safe dataframe operations.
        """

        question = user_input.lower()

        try:
            # --------------------------------
            # PROFIT QUESTIONS
            # --------------------------------
            if "profit" in question:
                if "laptop" in question:
                    total = (
                        self.df[self.df["Product"].str.lower() == "laptop"]
                        ["Profit"]
                        .sum()
                    )
                    return f"💰 Total profit from Laptops is {total:,.2f}"

                total_profit = self.df["Profit"].sum()
                return f"💰 Total profit is {total_profit:,.2f}"

            # --------------------------------
            # SALES QUESTIONS
            # --------------------------------
            if "sales" in question:
                total_sales = self.df["Sales_Amount"].sum()
                return f"📊 Total sales amount is {total_sales:,.2f}"

            # --------------------------------
            # TOP PRODUCTS
            # --------------------------------
            if "top" in question and "product" in question:
                top = (
                    self.df.groupby("Product")["Profit"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(3)
                )
                return "🏆 Top products by profit:\n" + top.to_string()

            # --------------------------------
            # FALLBACK
            # --------------------------------
            return (
                "🤔 I can help with questions about:\n"
                "- Profit\n"
                "- Sales\n"
                "- Top products\n\n"
                "Try: *What is the profit of laptops?*"
            )

        except Exception as e:
            return f"❌ Error while analyzing data: {e}"
