import asyncpg
import asyncio

async def test_connection():
    try:
        conn = await asyncpg.connect('postgresql://voice_user:voice_pass@localhost:5432/voice_ai')
        print('✅ Connected to PostgreSQL successfully')
        await conn.close()
        print('✅ Connection closed')
        return True
    except Exception as e:
        print(f'❌ Failed to connect to PostgreSQL: {e}')
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
