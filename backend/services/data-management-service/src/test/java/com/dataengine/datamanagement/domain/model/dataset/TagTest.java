package com.dataengine.datamanagement.domain.model.dataset;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class TagTest {

    @Test
    void usageCounter_inc_and_dec() {
        Tag t = new Tag("n", "d", null, "#fff");
        assertEquals(0L, t.getUsageCount());

        t.incrementUsage();
        assertEquals(1L, t.getUsageCount());

        t.decrementUsage();
        assertEquals(0L, t.getUsageCount());

        // 不会减到负数
        t.decrementUsage();
        assertEquals(0L, t.getUsageCount());
    }

    @Test
    void getters_setters() {
        Tag t = new Tag();
        t.setId("id");
        t.setName("name");
        t.setDescription("desc");
        t.setCategory("cat");
        t.setColor("#000");
        t.setUsageCount(5L);

        assertEquals("id", t.getId());
        assertEquals("name", t.getName());
        assertEquals("desc", t.getDescription());
        assertEquals("cat", t.getCategory());
        assertEquals("#000", t.getColor());
        assertEquals(5L, t.getUsageCount());
    }
}
