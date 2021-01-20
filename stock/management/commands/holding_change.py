from django.core.management.base import BaseCommand
from django.db import transaction, connection

class Command(BaseCommand):
    help = "Calculate StockHolding Daily Change"

    sql = """
    WITH daylookup AS 
    ( 
            SELECT   date, 
                    Lag(date, 1) OVER (ORDER BY date) AS prevdate 
            FROM     stock_weekday 
            WHERE    holiday IS false ) 
    UPDATE stock_stockholding 
    SET    daily_diff=t2.daily_diff, 
            daily_percent_diff=t2.daily_percent_diff
    FROM   ( 
                    SELECT      sh.id, 
                                sh.share-sh2.share                        AS daily_diff, 
                                ROUND((sh.share-sh2.share)*100/(sh2.total_shares+0.00000),5) AS daily_percent_diff
                    FROM       stock_stockholding sh 
                    INNER JOIN daylookup d 
                    ON         sh.date=d.date 
                    INNER JOIN stock_stockholding sh2 
                    ON         sh2.date=d.prevdate 
                    AND        sh.stock_id=sh2.stock_id 
                    AND        sh.participant_id=sh2.participant_id 
                    WHERE sh.daily_diff IS NULL
            ) AS t2
    WHERE  stock_stockholding.id=t2.id 
    """

    @transaction.atomic
    def handle(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute(self.sql)
