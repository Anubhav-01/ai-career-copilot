import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Progress } from "./progress";

describe("Progress", () => {
  it("exposes an accessible progressbar with clamped value", () => {
    render(<Progress value={150} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "100");
  });

  it("colors by score tone when requested", () => {
    const { container } = render(<Progress value={30} colorByScore />);
    expect(container.querySelector(".bg-rose-500")).not.toBeNull();
  });
});
