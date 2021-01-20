from django.core.management.base import BaseCommand
from django.db import transaction, connection

class Command(BaseCommand):
    help = "Calculate StockHolding Daily Change"

    sql = """
WITH 
daylookup AS 
( 
		SELECT   date, 
		lag(date, 1) OVER (ORDER BY date) AS prevdate 
		FROM     stock_weekday 
		WHERE    holiday IS false 
),

t2 AS 
( 
		SELECT  sh.id, 
				sh.share-sh2.share AS daily_diff, 
				ROUND((sh.share-sh2.share)*100/(sh2.total_shares+0.00000),10) AS daily_percent_diff 
		FROM   stock_stockholding sh 
		INNER JOIN daylookup d ON sh.date=d.date 
		INNER JOIN stock_stockholding sh2 ON sh2.date=d.prevdate AND sh.stock_id=sh2.stock_id AND sh.participant_id=sh2.participant_id 
		WHERE sh.daily_diff IS NULL 
)

		
UPDATE stock_stockholding 
SET    (daily_diff,daily_percent_diff)=(SELECT t2.daily_diff,t2.daily_percent_diff
FROM t2
WHERE  id=t2.id);

    """

    @transaction.atomic
    def handle(self, *args, **kwargs):
        text_file = open("Output.txt", "w")
        text_file.write(self.sql)
        text_file.close()

        cursor = connection.cursor()
        cursor.execute(self.sql)
        cursor.close()
